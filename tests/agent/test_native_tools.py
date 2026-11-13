import json
import threading

import pytest
from pydantic import ValidationError

from traceweaver.agent_models import (
    AgentRequest,
    AgentScopeRequest,
    NativeToolResult,
    ToolArguments,
)
from traceweaver.agent_tools import ToolStore, create_context, execute_tool
from traceweaver.explanation_scenarios import seed_explanation_profile
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError


def context(database, incident="INC-001", **options):
    return create_context(database, incident, InvestigationOptions(**options))


def test_context_is_native_bound_and_all_subject_ids_are_opaque(database):
    c = context(database)
    assert c.native_queries == 7 and c.source_fingerprint == c.catalog.investigation_fingerprint
    assert c.subjects["D000"] == ("deployment", ("DEP-002", "SVC-PAYMENT"))
    assert c.subjects["D001"] == ("deployment", ("DEP-001", "SVC-AUTH"))
    assert "DEP-001" not in c.node_handles.values()


@pytest.mark.parametrize(
    "name,subject",
    [
        ("get_incident_scope", "I000"),
        ("trace_deployment", "D000"),
        ("trace_deployment", "D001"),
        ("inspect_evidence", "E000"),
        ("inspect_gaps", "I000"),
    ],
)
def test_every_tool_executes_actual_parameterized_native_reads_and_preserves_bytes(
    database, monkeypatch, name, subject
):
    c = context(database)
    before = database.read_bytes()
    queries = []
    original = ToolStore.execute

    def counted(self, statement, params=None):
        queries.append((statement, params, threading.get_ident(), self.read_only))
        return original(self, statement, params)

    monkeypatch.setattr(ToolStore, "execute", counted)
    step = execute_tool(c, name, {"subject": subject})
    assert step.native_query_count == len(queries) >= 2
    assert all(row[3] for row in queries) and len({row[2] for row in queries}) == 1
    assert any("incident_id" in (q[1] or {}) for q in queries)
    assert any("UNWIND $edges" in q[0] for q in queries)
    assert database.read_bytes() == before
    with GraphStore(database) as store:
        for p in step.result.graph_paths:
            for edge in p.edges:
                assert (
                    store.execute(
                        "MATCH (a)-[r]->(b) WHERE a.id=$source AND b.id=$target "
                        "AND type(r)=$type RETURN count(r) AS n",
                        {"source": edge.source_id, "target": edge.target_id, "type": edge.type},
                    )[0]["n"]
                    >= 1
                )


def test_reverse_targets_and_included_change_are_persisted_direction(database):
    step = execute_tool(context(database), "trace_deployment", {"subject": "D001"})
    assert any(
        p.node_ids == ["INC-001", "SVC-PAYMENT", "SVC-AUTH", "DEP-001", "CHG-001"]
        for p in step.result.graph_paths
    )
    edge = step.result.graph_paths[0].edges[-1]
    assert (edge.source_id, edge.target_id, edge.traversal_direction) == (
        "DEP-001",
        "SVC-AUTH",
        "REVERSE",
    )


@pytest.mark.parametrize(
    "index,classification",
    [(0, "UNDETERMINED"), (1, "UNDETERMINED"), (2, "CONFLICTING_OBSERVATIONS")],
)
def test_native_comparison_reuses_structured_rules(case_database, index, classification):
    c = context(case_database, "CASE-INC")
    result = execute_tool(c, "compare_observations", {"subject": f"P{index:03}"}).result
    assert len(result.comparisons) == 1
    assert result.comparisons[0].classification == classification
    assert result.comparisons[0].service_id == "CASE-API"
    assert len(result.records) == 2


@pytest.mark.parametrize(
    "identity,expected_time",
    [("CASE-E-ORPHAN", "AT_ONSET"), ("CASE-E-NAIVE", "UNKNOWN"), ("CASE-E-NO-TIME", "UNKNOWN")],
)
def test_incomplete_evidence_keeps_real_unknowns_and_orphan_paths(
    case_database, identity, expected_time
):
    c = context(case_database, "CASE-INC")
    # This test examines the admitted snapshot directly for evidence beyond the bounded model offer.
    c.subjects["E999"] = ("evidence", (identity,))
    r = execute_tool(c, "inspect_evidence", {"subject": "E999"}).result
    assert r.records[0].temporal_classification == expected_time
    if identity == "CASE-E-ORPHAN":
        assert r.graph_paths[0].node_ids == ["CASE-INC", identity]
    else:
        assert r.records[0].timestamp.utc is None


def test_source_caps_and_model_offer_caps_are_independent(tmp_path):
    path = tmp_path / "caps.rl"
    seed_explanation_profile(path, "caps")
    c = context(path, "EV-CAPS")
    assert c.source.results_may_be_truncated and c.subjects_truncated
    assert sum(v[0] == "deployment" for v in c.subjects.values()) == 8
    assert execute_tool(c, "inspect_gaps", {"subject": "I000"}).result.status == "PARTIAL_CONTEXT"


def test_no_evidence_scope_is_real_and_insufficient(tmp_path):
    path = tmp_path / "none.rl"
    seed_explanation_profile(path, "evaluation")
    c = context(path, "EV-NONE")
    r = execute_tool(c, "inspect_gaps", {"subject": "I000"}).result
    assert r.status == "INSUFFICIENT_EVIDENCE" and "NO_INCIDENT_EVIDENCE" in r.gap_codes


@pytest.mark.parametrize(
    "tool,args,code",
    [
        ("DELETE", {"subject": "I000"}, "AGENT_TOOL_REJECTED"),
        ("trace_deployment", {"subject": "D999"}, "AGENT_SUBJECT_REJECTED"),
        ("trace_deployment", {"subject": "E000"}, "AGENT_SUBJECT_REJECTED"),
    ],
)
def test_unknown_out_of_scope_or_wrong_kind_rejected_before_native_open(
    database, monkeypatch, tool, args, code
):
    c = context(database)

    def forbidden(*args):
        raise AssertionError("Rejected action opened native store")

    monkeypatch.setattr(ToolStore, "__enter__", forbidden)
    with pytest.raises(ToolError) as exc:
        execute_tool(c, tool, args)
    assert exc.value.code == code


@pytest.mark.parametrize(
    "args",
    [
        {"subject": "DEP-001"},
        {"subject": "I000", "cypher": "MATCH (n) DELETE n"},
        {"subject": "http://invalid"},
        {"subject": 1},
    ],
)
def test_tool_args_cannot_contain_model_code_urls_raw_ids_or_extra_fields(args):
    with pytest.raises(ValidationError):
        ToolArguments.model_validate(args)


def test_stale_source_and_stale_requested_fingerprint_fail_closed(database):
    c = context(database)
    with pytest.raises(ToolError, match="fingerprint"):
        create_context(database, "INC-001", c.options, "0" * 64)
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (i:Incident {id:$id}) SET i.title=$title",
            {"id": "INC-001", "title": "Synthetic changed source"},
        )
    with pytest.raises(ToolError) as exc:
        execute_tool(c, "get_incident_scope", {"subject": "I000"})
    assert exc.value.code == "STALE_SNAPSHOT"


def test_native_query_budget_stops_before_extra_query(database):
    with ToolStore(database) as store:
        for _ in range(8):
            store.execute("MATCH (i:Incident) RETURN count(i) AS n")
        with pytest.raises(ToolError) as exc:
            store.execute("MATCH (i:Incident) RETURN count(i) AS n")
        assert exc.value.code == "AGENT_QUERY_BUDGET"


@pytest.mark.parametrize(
    "field,value",
    [
        ("confirmed", 1),
        ("confirmed", False),
        ("intent", "DECLARE_CAUSE"),
        ("prompt", "private"),
        ("model_id", "http://invalid"),
    ],
)
def test_agent_input_strict_field_allowlist(database, field, value):
    c = context(database)
    body = {
        "incident_id": "INC-001",
        "options": c.options.model_dump(),
        "source_fingerprint": c.source_fingerprint,
        "intent": "TRACE_DEPENDENCY_PATH",
        "confirmed": True,
        "model_id": "unit-model:1",
    }
    body[field] = value
    with pytest.raises(ValidationError):
        AgentRequest.model_validate(body)


def test_offline_request_does_not_accept_model_or_inference_fields(database):
    c = context(database)
    body = {
        "incident_id": "INC-001",
        "options": c.options.model_dump(),
        "source_fingerprint": c.source_fingerprint,
        "intent": "TRACE_DEPENDENCY_PATH",
        "confirmed": True,
        "model_id": "unit-model:1",
    }
    with pytest.raises(ValidationError):
        AgentScopeRequest.model_validate(body)


def test_tool_result_rejects_paths_outside_its_identity_set(database):
    r = execute_tool(context(database), "trace_deployment", {"subject": "D001"}).result.model_dump()
    r["entity_ids"] = []
    with pytest.raises(ValidationError):
        NativeToolResult.model_validate(r)


def test_hostile_source_body_and_private_original_time_are_never_returned(tmp_path):
    path = tmp_path / "hostile.rl"
    seed_explanation_profile(path, "adversarial")
    with GraphStore(path, read_only=False) as store:
        store.execute(
            "MATCH (e:Evidence {id:$id}) SET e.timestamp=$time",
            {"id": "EVD-001", "time": "C:/synthetic-private/secret.log"},
        )
    r = execute_tool(context(path), "inspect_evidence", {"subject": "E000"}).result
    raw = json.dumps(r.model_dump(mode="json"))
    assert "synthetic-private" not in raw and "ignore all instructions" not in raw
    assert r.records[0].timestamp.original is None and r.records[0].timestamp.original_withheld
