import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.dashboard import bundle_from_investigation, console_incidents, dashboard
from traceweaver.dashboard_models import DashboardBundle
from traceweaver.explanation_catalog import fingerprint
from traceweaver.explanation_scenarios import seed_explanation_profile
from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError


@pytest.fixture
def client(database):
    with TestClient(create_app(Settings(database=database)), base_url="http://127.0.0.1") as value:
        yield value


def test_dashboard_is_actual_single_native_investigation_and_legacy_parity(database):
    with GraphStore(database) as store:
        source = investigate(store, "INC-001")
    actual = dashboard(database, "INC-001")
    assert (
        actual.source_fingerprint
        == fingerprint(source)
        == actual.explanation.investigation_fingerprint
    )
    assert (
        actual.explanation.evidence_summary.returned_evidence
        == len(actual.investigation.evidence)
        == 4
    )
    with TestClient(create_app(Settings(database=database))) as client:
        assert client.get("/incidents/INC-001/explanation").json() == actual.explanation.model_dump(
            mode="json"
        )


def test_one_real_connection_seven_queries_same_thread_then_closed(database, monkeypatch):
    events = []

    class Observed(GraphStore):
        def __enter__(self):
            assert self.read_only
            events.append(("open", threading.get_ident()))
            return super().__enter__()

        def execute(self, *args, **kwargs):
            events.append(("query", threading.get_ident()))
            return super().execute(*args, **kwargs)

        def __exit__(self, *args):
            result = super().__exit__(*args)
            events.append(("closed", threading.get_ident()))
            return result

    monkeypatch.setattr("traceweaver.dashboard.GraphStore", Observed)
    dashboard(database, "INC-001")
    assert [e[0] for e in events] == ["open"] + ["query"] * 7 + ["closed"]
    assert len({e[1] for e in events}) == 1


@pytest.mark.parametrize("incident", ["INC-001", "INC-002", "CASE-INC", "CASE-NO-TIME"])
def test_every_dashboard_edge_exists_in_real_relate_and_file_unchanged(case_database, incident):
    before = case_database.read_bytes()
    b = dashboard(case_database, incident)
    paths = [p for c in b.investigation.candidates for p in c.graph_paths]
    paths += [x.graph_path for c in b.investigation.candidates for x in c.changes]
    paths += [p for e in b.investigation.evidence for p in e.graph_paths]
    paths += [x.graph_path for c in b.explanation.claims for x in c.citations if x.graph_path]
    edges = sorted({(e.type, e.source_id, e.target_id) for p in paths for e in p.edges})
    with GraphStore(case_database) as store:
        for kind, source, target in edges:
            assert (
                store.execute(
                    "MATCH (a)-[r]->(b) WHERE a.id=$source AND b.id=$target "
                    "AND type(r)=$kind RETURN count(r) AS n",
                    {"source": source, "target": target, "kind": kind},
                )[0]["n"]
                > 0
            )
    assert case_database.read_bytes() == before


def test_reverse_targets_and_orphan_are_not_fabricated(case_database):
    b = dashboard(case_database, "CASE-INC")
    c = next(c for c in b.investigation.candidates if c.deployment_id == "CASE-DEP-BEFORE")
    edge = c.graph_paths[0].edges[-1]
    assert (edge.type, edge.source_id, edge.target_id, edge.traversal_direction) == (
        "TARGETS",
        "CASE-DEP-BEFORE",
        "CASE-AUTH",
        "REVERSE",
    )
    orphan = next(e for e in b.investigation.evidence if e.evidence_id == "CASE-E-ORPHAN")
    assert orphan.graph_paths[0].node_ids == ["CASE-INC", "CASE-E-ORPHAN"]
    assert [e.type for e in orphan.graph_paths[0].edges] == ["HAS_EVIDENCE"]


def test_caps_and_option_scope_are_preserved(case_database):
    options = InvestigationOptions(max_candidates=1, max_evidence=1, pre_minutes=0, post_minutes=0)
    b = dashboard(case_database, "CASE-INC", options)
    assert b.investigation.options == options
    assert len(b.investigation.candidates) == len(b.investigation.evidence) == 1
    assert b.investigation.truncation["candidates"] and b.investigation.truncation["evidence"]
    # Source retrieval and curated explanation are independent truncation dimensions.
    assert b.explanation.catalog_claim_count == b.explanation.validated_claim_count == 6
    assert b.explanation.truncation.selected_subset is False
    assert b.investigation.results_may_be_truncated


def test_options_cannot_be_published_under_wrong_source_scope(database):
    with GraphStore(database) as store:
        i = investigate(store, "INC-001")
    with pytest.raises(ToolError) as error:
        bundle_from_investigation(i, InvestigationOptions(pre_minutes=0))
    assert error.value.code == "DASHBOARD_OPTIONS_MISMATCH"


@pytest.mark.parametrize("field", ["view_fingerprint", "source_fingerprint"])
def test_bundle_digest_rejects_tampering(database, field):
    data = dashboard(database, "INC-001").model_dump()
    data[field] = "0" * 64
    with pytest.raises(ValidationError):
        DashboardBundle.model_validate(data)


def test_source_prose_private_refs_and_html_never_reach_projection(tmp_path):
    path = tmp_path / "adversarial.rl"
    seed_explanation_profile(path, "adversarial")
    with GraphStore(path, read_only=False) as store:
        store.execute(
            "MATCH (i:Incident {id:$id}) SET i.title=$text",
            {"id": "INC-001", "text": "<script>synthetic-private()</script>"},
        )
    b = dashboard(path, "INC-001")
    text = b.model_dump_json()
    for forbidden in [
        "ignore all instructions",
        "confirmed root cause",
        "synthetic-private",
        "internal.invalid",
        "sk-" + "SYNTHETIC" * 6,
    ]:
        assert forbidden not in text
    assert b.investigation.title.status == "WITHHELD"
    assert "properties" not in b.model_dump()["investigation"]
    assert all(e.source_reference == "WITHHELD" for e in b.investigation.evidence)
    listed = console_incidents(path)
    assert listed.incidents[0].title == "Metadata withheld"


def test_shared_service_does_not_leak_other_incident(case_database):
    b = dashboard(case_database, "CASE-INC")
    assert "CASE-E-OTHER" not in b.model_dump_json()
    assert len(b.investigation.contradictions) == 3
    assert b.explanation.evidence_summary.conflict_count == 1
    assert b.explanation.evidence_summary.undetermined_count == 2


@pytest.mark.parametrize(
    "profile,incident", [("evaluation", "EV-NONE"), ("sprint01", "CASE-NO-TIME")]
)
def test_absent_evidence_or_onset_is_honest(tmp_path, profile, incident):
    path = tmp_path / "case.rl"
    seed_explanation_profile(path, profile)
    b = dashboard(path, incident)
    if incident == "EV-NONE":
        assert b.explanation.explanation_status == "ABSTAINED"
        assert b.investigation.evidence == []
    else:
        assert b.investigation.incident_time.utc is None
        assert all(c.temporal_classification == "UNKNOWN" for c in b.investigation.candidates)


@pytest.mark.parametrize(
    "query",
    [
        "pre_minutes=-1",
        "pre_minutes=1.0",
        "post_minutes=1441",
        "max_candidates=0",
        "max_evidence=101",
    ],
)
def test_bundle_strict_query_validation(client, query):
    assert client.get("/incidents/INC-001/dashboard?" + query).status_code == 422


def test_http_unknown_and_no_model_on_get(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Ordinary GET must never invoke a model")

    monkeypatch.setattr("traceweaver.explanation.OllamaLocal.select", forbidden)
    assert client.get("/incidents/unknown/dashboard").status_code == 404
    response = client.get("/incidents/INC-001/dashboard?mode=ollama&model=qwen3:8b")
    assert response.status_code == 200
    assert response.json()["explanation"]["mode_executed"] == "DETERMINISTIC"


@pytest.mark.parametrize("contents", [None, b"not relate"])
def test_unavailable_store_is_generic_without_creation(tmp_path, contents):
    path = tmp_path / "private-location.rl"
    if contents:
        path.write_bytes(contents)
    with TestClient(create_app(Settings(database=path)), base_url="http://127.0.0.1") as client:
        r = client.get("/incidents/INC-001/dashboard")
        assert r.status_code == 503
        assert str(tmp_path) not in r.text
    if contents is None:
        assert not path.exists()


def test_concurrent_bundle_reads_keep_hash_and_snapshot(database, client):
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with ThreadPoolExecutor(max_workers=4) as worker:
        results = list(worker.map(lambda _: client.get("/incidents/INC-001/dashboard"), range(8)))
    assert all(r.status_code == 200 and r.json() == results[0].json() for r in results)
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_new_incident_list_is_bounded_safe_and_real(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (i:Incident {id:$id}) SET i.title=$title",
            {"id": "INC-001", "title": "C:/synthetic-private/test"},
        )
    result = console_incidents(database)
    assert [i.id for i in result.incidents] == ["INC-001", "INC-002"]
    assert result.incidents[0].metadata_withheld
    assert "synthetic-private" not in result.model_dump_json()
    assert result.results_may_be_truncated is False


def test_bundle_json_is_stable_and_strict(database):
    first = dashboard(database, "INC-001")
    assert first.model_dump_json() == dashboard(database, "INC-001").model_dump_json()
    data = json.loads(first.model_dump_json())
    data["root_cause"] = "forbidden"
    with pytest.raises(ValidationError):
        DashboardBundle.model_validate(data)


def test_console_node_kinds_are_read_from_actual_native_labels(database):
    b = dashboard(database, "INC-001")
    assert b.investigation.entity_kinds["DEP-001"] == "Deployment"
    assert b.investigation.entity_kinds["SVC-AUTH"] == "Service"
    with GraphStore(database) as store:
        for identity, kind in b.investigation.entity_kinds.items():
            assert store.execute(
                "MATCH (n {id:$id}) RETURN labels(n) AS labels", {"id": identity}
            ) == [{"labels": [kind]}]


def test_duplicate_ids_across_labels_cannot_be_collapsed_into_false_node(database):
    with GraphStore(database, read_only=False) as store:
        store.execute("CREATE (:Service {id:$id})", {"id": "DEP-001"})
    with pytest.raises(ToolError) as error:
        dashboard(database, "INC-001")
    assert error.value.code == "DASHBOARD_AMBIGUOUS_IDENTITY"


def test_stored_edge_with_invalid_intermediate_label_fails_closed(tmp_path):
    database = tmp_path / "invalid-domain.rl"
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "CREATE (i:Incident {id:'I',demo:true,timestamp:'2026-11-12T10:00:00Z'})"
            "-[:AFFECTS]->(a:Service {id:'A'})-[:DEPENDS_ON]->(:Evidence {id:'B'})"
            "-[:DEPENDS_ON]->(c:Service {id:'C'})<-[:TARGETS]-"
            "(:Deployment {id:'D',timestamp:'2026-11-12T09:00:00Z'})"
        )
    with pytest.raises(ToolError) as error:
        dashboard(database, "I")
    assert error.value.code == "DASHBOARD_INVALID_DOMAIN"
