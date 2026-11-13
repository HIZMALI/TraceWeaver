import json
from typing import get_args

import pytest

from traceweaver.agent_cli import main
from traceweaver.agent_models import AgentScopeRequest, Intent, canonical_agent_payload
from traceweaver.agent_rehearsal import fixed_plan, run_rehearsal
from traceweaver.agent_tools import create_context
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError


def action(database, incident="INC-001", intent="TRACE_DEPENDENCY_PATH", **options):
    c = create_context(database, incident, InvestigationOptions(**options))
    return AgentScopeRequest(
        incident_id=incident,
        options=c.options,
        source_fingerprint=c.source_fingerprint,
        intent=intent,
        confirmed=True,
    )


@pytest.mark.parametrize("intent", get_args(Intent))
def test_all_offline_plans_are_native_repeatable_and_never_ai(case_database, monkeypatch, intent):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline rehearsal contacted a model")

    monkeypatch.setattr("traceweaver.agent_provider.AgentProvider.chat", forbidden)
    before = case_database.read_bytes()
    request = action(case_database, "CASE-INC", intent)
    a, b = run_rehearsal(case_database, request), run_rehearsal(case_database, request)
    assert canonical_agent_payload(a) == canonical_agent_payload(b)
    assert 2 <= len(a.tool_trace) <= 4 and a.native_query_count > 7
    assert all(s.native_query_count >= 2 and s.result.graph_paths for s in a.tool_trace)
    assert not a.ai_directed_tools and not a.ai_generated_selection and a.model_interactions == 0
    assert a.validated_claims[-1].claim_type == "NO_CAUSAL_VERDICT"
    assert case_database.read_bytes() == before


def test_dependency_plan_prefers_deep_path_and_keeps_reverse_targets(database):
    report = run_rehearsal(database, action(database))
    step = next(s for s in report.tool_trace if s.tool_name == "trace_deployment")
    assert step.subject_ids == ["DEP-001", "SVC-AUTH"]
    assert any(
        e.type == "TARGETS" and e.traversal_direction == "REVERSE"
        for p in step.result.graph_paths
        for e in p.edges
    )


def test_reconciliation_prefers_actual_conflict_not_unknown_pair(case_database):
    report = run_rehearsal(
        case_database, action(case_database, "CASE-INC", "RECONCILE_OBSERVATIONS")
    )
    comparisons = [p for s in report.tool_trace for p in s.result.comparisons]
    assert comparisons[0].classification == "CONFLICTING_OBSERVATIONS"
    assert comparisons[1].classification == "UNDETERMINED"


def test_cap_honesty_survives_offline_rehearsal(case_database):
    report = run_rehearsal(
        case_database, action(case_database, "CASE-INC", max_evidence=1, max_candidates=1)
    )
    assert report.source_truncated and report.agent_status == "PARTIAL_CONTEXT"
    assert any(s.result.truncated for s in report.tool_trace)


def test_missing_evidence_abstains_on_real_store(tmp_path):
    database = tmp_path / "no-evidence.rl"
    with GraphStore(database, read_only=False) as store:
        store.execute("CREATE (:Incident {id:'NONE-INC', demo:true})")
    report = run_rehearsal(database, action(database, "NONE-INC"))
    assert report.agent_status == "ABSTAINED"
    assert not any(c.claim_type == "EVIDENCE_REPORTED" for c in report.validated_claims)


def test_stale_request_aborts_before_native_tool(database):
    request = action(database).model_copy(update={"source_fingerprint": "0" * 64})
    with pytest.raises(ToolError, match="stale"):
        run_rehearsal(database, request)


def test_invalid_fixed_intent_is_not_a_plan(database):
    with pytest.raises(ToolError):
        fixed_plan(create_context(database, "INC-001", InvestigationOptions()), "WRITE")


def test_cli_canonical_outputs_are_equal_and_read_only(database, capsys):
    args = [
        "--database",
        str(database),
        "--incident",
        "INC-001",
        "--intent",
        "FIND_EVIDENCE_GAPS",
        "--rehearse",
        "--canonical",
    ]
    before = database.read_bytes()
    assert main(args) == 0
    a = capsys.readouterr().out
    assert main(args) == 0
    assert a == capsys.readouterr().out and "elapsed_ms" not in json.loads(a)
    assert database.read_bytes() == before


def test_cli_model_requires_explicit_confirmation(database):
    with pytest.raises(SystemExit) as failure:
        main(
            [
                "--database",
                str(database),
                "--incident",
                "INC-001",
                "--intent",
                "FIND_EVIDENCE_GAPS",
                "--model",
                "qwen3:8b",
            ]
        )
    assert failure.value.code == 2


def test_cli_missing_store_never_creates_database(tmp_path, capsys):
    target = tmp_path / "absent.rl"
    assert (
        main(
            [
                "--database",
                str(target),
                "--incident",
                "INC-001",
                "--intent",
                "FIND_EVIDENCE_GAPS",
                "--rehearse",
            ]
        )
        == 14
    )
    assert not target.exists() and str(tmp_path) not in capsys.readouterr().err
