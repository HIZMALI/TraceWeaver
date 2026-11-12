import json
from importlib.resources import files
from pathlib import Path

import pytest
from pydantic import ValidationError

from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.queries import IncidentNotFound
from traceweaver.seed import seed_database
from traceweaver.storage import GraphStore, QueryError


def read(database, id="CASE-INC", **options):
    with GraphStore(database) as store:
        return investigate(store, id, InvestigationOptions(**options))


def test_baseline_investigation_real_graph_and_no_fabricated_conflicts(database):
    before = database.read_bytes()
    result = read(database, "INC-001")
    assert result.incident_started_at == "2026-11-10T10:05:00Z"
    candidate = next(c for c in result.candidates if c.deployment_id == "DEP-001")
    assert candidate.dependency_depth == 1
    path = candidate.changes[0].graph_path
    assert path.node_ids == ["INC-001", "SVC-PAYMENT", "SVC-AUTH", "DEP-001", "CHG-001"]
    assert [edge.type for edge in path.edges] == [
        "AFFECTS",
        "DEPENDS_ON",
        "TARGETS",
        "INCLUDES_CHANGE",
    ]
    assert path.edges[2].source_id == "DEP-001"
    assert path.edges[2].target_id == "SVC-AUTH"
    assert path.edges[2].traversal_direction == "REVERSE"
    assert result.contradictions == []
    assert result.contradiction_audit.not_evaluable_count == 4
    assert result.causal_conclusion == "NOT_ESTABLISHED"
    assert result.provenance_audit.traceable_count == 4
    assert result.investigation_status == "PARTIAL_CONTEXT"
    assert database.read_bytes() == before
    example = Path(__file__).resolve().parents[1] / "docs/examples/INC-001-investigation.json"
    assert result.model_dump(mode="json") == json.loads(example.read_text())


def test_temporal_candidates_remain_visible_without_causal_ranking(case_database):
    result = read(case_database)
    candidates = {c.deployment_id: c for c in result.candidates}
    assert candidates["CASE-DEP-BEFORE"].temporal_classification == "BEFORE"
    assert candidates["CASE-DEP-BEFORE"].candidate_assessment == "INVESTIGATE"
    after = candidates["CASE-DEP-AFTER"]
    assert after.temporal_classification == "AFTER"
    assert after.candidate_assessment == "TEMPORALLY_EXCLUDED"
    assert candidates["CASE-DEP-ONSET"].temporal_classification == "AT_ONSET"
    assert candidates["CASE-DEP-OFFSET"].temporal_classification == "AT_ONSET"
    assert candidates["CASE-DEP-INVALID"].candidate_assessment == "INSUFFICIENT_DATA"
    assert result.causal_conclusion == "NOT_ESTABLISHED"


def test_unrelated_deployment_excluded_and_missing_change_candidate_retained(case_database):
    result = read(case_database)
    assert "CASE-DEP-UNRELATED" not in {c.deployment_id for c in result.candidates}
    candidate = next(c for c in result.candidates if c.deployment_id == "CASE-DEP-NOCHANGE")
    assert candidate.changes == [] and candidate.change_ids == []
    assert candidate.graph_paths[0].node_ids == ["CASE-INC", "CASE-API", "CASE-DEP-NOCHANGE"]


@pytest.mark.parametrize("anchor", [None, "invalid", "2026-11-12T10:00:00"])
def test_missing_or_invalid_onset_returns_unknown_partial_context(case_database, anchor):
    with GraphStore(case_database, read_only=False) as store:
        store.execute(
            "MATCH (i:Incident {id: $id}) SET i.incident_started_at = $anchor",
            {"id": "CASE-NO-TIME", "anchor": anchor},
        )
    result = read(case_database, "CASE-NO-TIME")
    assert result.incident_started_at is None
    assert result.investigation_status == "PARTIAL_CONTEXT"
    assert all(c.temporal_classification == "UNKNOWN" for c in result.candidates)
    assert all(c.candidate_assessment == "INSUFFICIENT_DATA" for c in result.candidates)
    assert result.incident_time.warning_code in {"MISSING_TIMESTAMP", "INVALID_TIMESTAMP"}


def test_incident_evidence_isolation_even_with_shared_service(case_database):
    main = read(case_database)
    other = read(case_database, "CASE-OTHER")
    assert "CASE-E-OTHER" not in {e.evidence_id for e in main.evidence}
    assert [e.evidence_id for e in other.evidence] == ["CASE-E-OTHER"]
    assert other.contradictions == []
    assert all(e.graph_paths[0].node_ids[0] == "CASE-OTHER" for e in other.evidence)


def test_incomplete_invalid_and_orphan_evidence_are_not_lost(case_database):
    result = read(case_database)
    evidence = {e.evidence_id: e for e in result.evidence}
    assert evidence["CASE-E-NAIVE"].provenance_status == "INVALID"
    assert evidence["CASE-E-NAIVE"].temporal_classification == "UNKNOWN"
    assert evidence["CASE-E-NO-TIME"].provenance_status == "INCOMPLETE"
    assert evidence["CASE-E-MISSING-REF"].provenance_status == "INCOMPLETE"
    orphan = evidence["CASE-E-ORPHAN"]
    assert orphan.observed_service_ids == []
    assert orphan.graph_paths[0].node_ids == ["CASE-INC", "CASE-E-ORPHAN"]
    assert any(w.code == "MISSING_OBSERVED_SERVICE" for w in orphan.warnings)
    audit = result.provenance_audit
    assert (
        audit.total_evidence == audit.traceable_count + audit.incomplete_count + audit.invalid_count
    )
    assert audit.total_evidence == 11


def test_traceability_is_separate_from_external_verification(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (e:Evidence {id: $id}) SET e.demo = false, e.source_ref = $ref",
            {"id": "EVD-001", "ref": "https://example.invalid/observation/original"},
        )
    result = read(database, "INC-001")
    item = next(e for e in result.evidence if e.evidence_id == "EVD-001")
    assert item.provenance_status == "TRACEABLE"
    assert item.verification_status == "UNVERIFIED_EXTERNAL"
    assert item.source_ref == "https://example.invalid/observation/original"
    assert result.provenance_audit.unverified_external_count == 1
    assert result.provenance_audit.traceable_count == 4


def test_invalid_source_type_is_audit_data_not_http_model_failure(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (e:Evidence {id: $id}) SET e.source = $value", {"id": "EVD-001", "value": 42}
        )
    result = read(database, "INC-001")
    item = next(e for e in result.evidence if e.evidence_id == "EVD-001")
    assert item.source == 42
    assert item.provenance_status == "INVALID"
    assert any(w.code == "INVALID_SOURCE" for w in item.warnings)


def test_non_json_engine_metadata_remains_visibly_invalid(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (e:Evidence {id: $id}) "
            "SET e.source = date('2026-11-12'), e.timestamp = date('2026-11-12')",
            {"id": "EVD-001"},
        )
    result = read(database, "INC-001")
    item = next(e for e in result.evidence if e.evidence_id == "EVD-001")
    assert item.source == {"unsupported_type": "date", "representation": "2026-11-12"}
    assert item.evidence_observed_at.warning_code == "INVALID_TIMESTAMP"
    assert item.provenance_status == "INVALID"


def test_duplicate_source_reference_is_warning_not_a_contradiction(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (e:Evidence {id: $id}) SET e.source_ref = $ref",
            {"id": "EVD-002", "ref": "demo://evidence/EVD-001"},
        )
    result = read(database, "INC-001")
    assert any(w.code == "DUPLICATE_SOURCE_REFERENCE" for w in result.provenance_audit.warnings)
    assert result.contradictions == []


def test_structured_conflicts_and_degraded_uncertainty(case_database):
    result = read(case_database)
    conflicts = [c for c in result.contradictions if c.classification == "CONFLICTING_OBSERVATIONS"]
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert set(conflict.evidence_ids) == {"CASE-E-HEALTHY", "CASE-E-FAILED"}
    assert conflict.signal_key == "availability" and conflict.service_id == "CASE-API"
    assert conflict.overlap_window == {
        "start": "2026-11-12T09:59:00Z",
        "end": "2026-11-12T10:01:00Z",
    }
    assert result.contradiction_audit.conflict_count == 1
    assert result.contradiction_audit.undetermined_count == 2
    assert not any(
        "CASE-E-EARLY" in c.evidence_ids or "CASE-E-LATE" in c.evidence_ids
        for c in result.contradictions
    )
    assert not any("CASE-E-WRONG-SERVICE" in c.evidence_ids for c in result.contradictions)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("environment", "different-environment"),
        ("signal_key", "different-signal"),
        ("observation_window_start", "2026-11-12T11:00:00Z"),
        ("observed_state", "UNRECOGNIZED"),
        ("service_id", "CASE-AUTH"),
    ],
)
def test_incomparable_or_invalid_structured_data_does_not_conflict(case_database, field, value):
    with GraphStore(case_database, read_only=False) as store:
        # Property name is chosen from this test's fixed allowlist, values remain bound.
        store.execute(
            f"MATCH (e:Evidence {{id: $id}}) SET e.{field} = $value",
            {"id": "CASE-E-FAILED", "value": value},
        )
        if field == "service_id":
            store.execute(
                "MATCH (e:Evidence {id: $id}), (s:Service {id: $service}) "
                "MERGE (e)-[:OBSERVED_ON]->(s)",
                {"id": "CASE-E-FAILED", "service": value},
            )
        if field == "observation_window_start":
            store.execute(
                "MATCH (e:Evidence {id: $id}) SET e.observation_window_end = $end",
                {"id": "CASE-E-FAILED", "end": "2026-11-12T11:01:00Z"},
            )
    result = read(case_database)
    assert result.contradiction_audit.conflict_count == 0


def test_cycle_paths_deduplicate_and_choose_real_shortest_path(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (a:Service {id: $a}), (p:Service {id: $p}) MERGE (a)-[:DEPENDS_ON]->(p)",
            {"a": "SVC-AUTH", "p": "SVC-PAYMENT"},
        )
    first, second = read(database, "INC-001"), read(database, "INC-001")
    assert first.model_dump() == second.model_dump()
    assert len(first.candidates) == 2
    for candidate in first.candidates:
        for path in candidate.graph_paths:
            assert len(path.node_ids) == len(set(path.node_ids))
    assert (
        len(next(c for c in first.candidates if c.deployment_id == "DEP-001").graph_paths[0].edges)
        == 3
    )


def test_truncation_uses_lookahead_not_exact_limit(database):
    exact = read(database, "INC-001", max_candidates=2, max_evidence=4)
    assert exact.results_may_be_truncated is False
    fewer = read(database, "INC-001", max_candidates=1, max_evidence=3)
    assert len(fewer.candidates) == 1 and len(fewer.evidence) == 3
    assert fewer.truncation["candidates"] and fewer.truncation["evidence"]
    assert fewer.results_may_be_truncated
    assert fewer.provenance_audit.total_evidence == 3


def test_large_graph_list_caps_and_batched_access(database):
    with GraphStore(database, read_only=False) as store:
        with store.transaction():
            for n in range(101):
                store.execute(
                    "MATCH (s:Service {id: $service}), (i:Incident {id: $incident}) "
                    "CREATE (:Deployment {id: $deployment, timestamp: $time})-[:TARGETS]->(s), "
                    "(i)-[:HAS_EVIDENCE]->(:Evidence {id: $evidence, timestamp: $time})",
                    {
                        "service": "SVC-PAYMENT",
                        "incident": "INC-001",
                        "deployment": f"BULK-D-{n:03}",
                        "evidence": f"BULK-E-{n:03}",
                        "time": "2026-11-10T10:00:00Z",
                    },
                )

    class CountingStore(GraphStore):
        calls = 0

        def execute(self, *args, **kwargs):
            self.calls += 1
            return super().execute(*args, **kwargs)

    with CountingStore(database) as store:
        result = investigate(store, "INC-001")
        assert store.calls == 6
    assert len(result.candidates) == len(result.evidence) == len(result.timeline) == 100
    assert (
        result.truncation["candidates"]
        and result.truncation["evidence"]
        and result.truncation["timeline"]
    )


def test_additive_fixture_idempotency_packaging_and_user_data_preservation(case_database):
    path = Path(__file__).resolve().parents[1] / "fixtures/sprint01_cases.json"
    assert json.loads(path.read_text()) == json.loads(
        files("traceweaver").joinpath("fixtures/sprint01_cases.json").read_text()
    )
    with GraphStore(case_database, read_only=False) as store:
        store.execute("CREATE (:UserNote {id: 'sprint01-user-note', text: 'keep me'})")
    for _ in range(2):
        assert seed_database(case_database, path) == {"node_count": 52, "relationship_count": 67}
    read(case_database)
    with GraphStore(case_database) as store:
        assert store.execute(
            "MATCH (n:UserNote {id: $id}) RETURN n.text AS text LIMIT 1",
            {"id": "sprint01-user-note"},
        ) == [{"text": "keep me"}]


def test_additive_import_conflict_rolls_back_new_incidents(database):
    path = Path(__file__).resolve().parents[1] / "fixtures/sprint01_cases.json"
    with GraphStore(database, read_only=False) as store:
        store.execute("CREATE (:Service {id: 'CASE-AUTH', name: 'User-owned conflict'})")
    with pytest.raises(QueryError, match="Seed conflict"):
        seed_database(database, path)
    with GraphStore(database) as store:
        assert store.counts() == {"node_count": 22, "relationship_count": 27}
        assert (
            store.execute(
                "MATCH (i:Incident {id: $id}) RETURN i.id AS id LIMIT 1", {"id": "CASE-INC"}
            )
            == []
        )


def test_empty_evidence_has_explicit_insufficient_status(tmp_path):
    path = tmp_path / "empty-evidence.rl"
    with GraphStore(path, read_only=False) as store:
        store.execute("CREATE (:Incident {id: 'EMPTY', demo: true})")
    result = read(path, "EMPTY")
    assert result.evidence == [] and result.provenance_audit.total_evidence == 0
    assert result.investigation_status == "INSUFFICIENT_EVIDENCE"
    assert result.causal_conclusion == "NOT_ESTABLISHED"
    assert "NO_INCIDENT_EVIDENCE" in result.status_reasons


def test_injection_shaped_id_does_not_return_an_incident(database):
    with pytest.raises(IncidentNotFound):
        read(database, "INC-001' OR true //")


def test_three_dependency_hops_include_target_and_four_hops_exclude_it(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (s:Service {id: $id}) "
            "CREATE (s)-[:DEPENDS_ON]->(a:Service {id:'DEEP-1'})"
            "-[:DEPENDS_ON]->(b:Service {id:'DEEP-2'})"
            "-[:DEPENDS_ON]->(c:Service {id:'DEEP-3'}), "
            "(:Deployment {id:'DEP-DEPTH-3'})-[:TARGETS]->(b), "
            "(:Deployment {id:'DEP-DEPTH-4'})-[:TARGETS]->(c)",
            {"id": "SVC-LEDGER"},
        )
    result = read(database, "INC-001")
    candidates = {c.deployment_id: c for c in result.candidates}
    assert candidates["DEP-DEPTH-3"].dependency_depth == 3
    assert candidates["DEP-DEPTH-3"].graph_paths[0].node_ids == [
        "INC-001",
        "SVC-PAYMENT",
        "SVC-LEDGER",
        "DEEP-1",
        "DEEP-2",
        "DEP-DEPTH-3",
    ]
    assert "DEP-DEPTH-4" not in candidates


def test_many_structured_conflicts_are_bounded_and_audit_counts_remain_exact(database):
    with GraphStore(database, read_only=False) as store:
        with store.transaction():
            for n in range(22):
                properties = {
                    "id": f"CONFLICT-{n:02}",
                    "demo": True,
                    "source": "demo-signal",
                    "source_ref": f"demo://conflict/{n}",
                    "timestamp": "2026-11-10T10:05:00Z",
                    "signal_key": "availability",
                    "observed_state": "HEALTHY" if n < 11 else "FAILED",
                    "service_id": "SVC-PAYMENT",
                    "environment": "demo",
                }
                store.execute(
                    "MATCH (i:Incident {id: $incident}), (s:Service {id: $service}) "
                    "CREATE (i)-[:HAS_EVIDENCE]->(e:Evidence)-[:OBSERVED_ON]->(s) "
                    "SET e += $properties",
                    {"incident": "INC-001", "service": "SVC-PAYMENT", "properties": properties},
                )
    result = read(database, "INC-001")
    assert result.contradiction_audit.conflict_count == 121
    assert len(result.contradictions) == 100
    assert result.truncation["contradictions"]
    assert result.results_may_be_truncated


def test_auxiliary_observation_and_change_caps_report_actual_lookahead(database):
    with GraphStore(database, read_only=False) as store:
        with store.transaction():
            for n in range(101):
                store.execute(
                    "MATCH (e:Evidence {id: $evidence}), (d:Deployment {id: $deployment}) "
                    "CREATE (e)-[:OBSERVED_ON]->(:Service {id: $service}), "
                    "(d)-[:INCLUDES_CHANGE]->(:Change {id: $change})",
                    {
                        "evidence": "EVD-001",
                        "deployment": "DEP-001",
                        "service": f"OBS-{n:03}",
                        "change": f"CHG-BULK-{n:03}",
                    },
                )
    result = read(database, "INC-001")
    assert (
        len(result.evidence) == 4
    )  # Evidence nodes remain visible even if observations are capped.
    assert result.truncation["observations"] and result.truncation["changes"]
    assert sum(len(e.observed_service_ids) for e in result.evidence) == 100
    assert len(next(c for c in result.candidates if c.deployment_id == "DEP-001").changes) == 100


def test_complete_structured_observation_can_be_ready_without_a_causal_conclusion(tmp_path):
    path = tmp_path / "review-ready.rl"
    with GraphStore(path, read_only=False) as store:
        store.execute(
            "CREATE (i:Incident {id:'REVIEW', demo:true, timestamp:'2026-11-12T10:00:00Z'})"
            "-[:AFFECTS]->(s:Service {id:'REVIEW-SERVICE'}), "
            "(i)-[:HAS_EVIDENCE]->(e:Evidence {id:'REVIEW-EVIDENCE', demo:true, "
            "source:'demo-observer', source_ref:'demo://review', timestamp:'2026-11-12T10:00:00Z', "
            "signal_key:'availability', observed_state:'HEALTHY', service_id:'REVIEW-SERVICE', "
            "environment:'demo'})-[:OBSERVED_ON]->(s)"
        )
    result = read(path, "REVIEW")
    assert result.investigation_status == "READY_FOR_REVIEW"
    assert result.data_quality.status == "COMPLETE"
    assert result.causal_conclusion == "NOT_ESTABLISHED"


@pytest.mark.parametrize("modification", ["version_one", "not_demo"])
def test_incomplete_specimens_require_explicit_version_and_demo_identity(tmp_path, modification):
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures/sprint01_cases.json").read_text()
    )
    if modification == "version_one":
        data["schema_version"] = 1
    else:
        data["nodes"][0]["properties"]["demo"] = False
    fixture = tmp_path / "invalid-specimen.json"
    fixture.write_text(json.dumps(data))
    store = tmp_path / "not-created.rl"
    with pytest.raises(ValidationError):
        seed_database(store, fixture)
    assert not store.exists()
