"""CONTROLLED protocol hypotheses and native boundary regressions, never live Qwen evidence."""

import json

import pytest

from traceweaver.agent import (
    admit_finish,
    offered_claim_metadata,
    retrieved_claims,
    run_agent,
)
from traceweaver.agent_diagnostics import StructuralDiagnostics, probe_local_ollama
from traceweaver.agent_models import AgentRequest
from traceweaver.agent_provider import AgentFinalProposal
from traceweaver.agent_tools import create_context, execute_tool
from traceweaver.explanation_scenarios import seed_explanation_profile
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.ollama_local import OllamaFailure, OllamaLocal
from traceweaver.tool_errors import ToolError

MODEL = "controlled-06b:1"
PRIVATE = "SYNTHETIC_PRIVATE_DO_NOT_PERSIST_https://invalid.example/private"


def context(database):
    return create_context(database, "INC-001", InvestigationOptions())


def request(database):
    c = context(database)
    return AgentRequest(
        incident_id=c.source.incident_id,
        options=c.options,
        source_fingerprint=c.source_fingerprint,
        intent="TRACE_DEPENDENCY_PATH",
        confirmed=True,
        model_id=MODEL,
    )


def controlled(monkeypatch, *, count=2, final_change=None, tool_message=None, failure=None):
    requests = []
    choices = [
        ("get_incident_scope", "I000"),
        ("trace_deployment", "D001"),
        ("inspect_evidence", "E000"),
        ("inspect_gaps", "I000"),
    ]

    def transport(self, method, route, payload=None, *, deadline=None):
        if route == "/api/tags":
            return {"models": [{"name": MODEL, "size": 1}]}
        requests.append(json.loads(json.dumps(payload)))
        if failure:
            raise failure
        if "format" not in payload and len(requests) <= count:
            name, subject = choices[len(requests) - 1]
            message = {
                "role": "assistant",
                "content": "",
                "thinking": PRIVATE,
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"index": 0, "name": name, "arguments": {"subject": subject}},
                    }
                ],
            }
            if tool_message:
                message = tool_message(message)
        elif "format" not in payload:
            message = {"role": "assistant", "content": "", "thinking": PRIVATE}
        else:
            packet = json.loads(payload["messages"][-1]["content"])
            ids = [c["claim_id"] for c in packet["retrieved_claims"]][:8]
            body = dict(
                investigation_fingerprint=packet["investigation_fingerprint"],
                selected_claim_ids=ids,
                focus="BALANCED",
                abstain=not ids,
                tool_steps=packet["executed_steps"],
            )
            message = {"role": "assistant", "content": json.dumps(body), "thinking": PRIVATE}
            if final_change:
                message = final_change(message, body)
        return {
            "done": True,
            "done_reason": "stop",
            "model": MODEL,
            "message": message,
            "eval_count": 25,
            "prompt_eval_count": 300,
        }

    monkeypatch.setattr(OllamaLocal, "_request", transport)
    return requests


def test_controlled_two_distinct_native_tools_strict_finish_and_private_metadata_sink(
    database, monkeypatch
):
    payloads = controlled(monkeypatch)
    before = database.read_bytes()
    diagnostic = StructuralDiagnostics()
    report = run_agent(database, request(database), diagnostics=diagnostic)
    assert [s.tool_name for s in report.tool_trace] == ["get_incident_scope", "trace_deployment"]
    assert report.ai_directed_tools and report.ai_generated_selection
    assert any(c.claim_type == "DEPLOYMENT_CONNECTED" for c in report.validated_claims)
    assert any(
        e.type == "TARGETS"
        and e.traversal_direction == "REVERSE"
        and e.source_id == "DEP-001"
        and e.target_id == "SVC-AUTH"
        for s in report.tool_trace
        for p in s.result.graph_paths
        for e in p.edges
    )
    assert database.read_bytes() == before
    assert PRIVATE not in json.dumps(payloads) and PRIVATE not in json.dumps(diagnostic.export())
    assert PRIVATE not in report.model_dump_json()
    next_history = payloads[1]["messages"]
    assert next_history[-2]["role"] == "assistant"
    assert next_history[-2]["tool_calls"][0]["function"] == {
        "name": "get_incident_scope",
        "arguments": {"subject": "I000"},
    }
    assert (
        next_history[-1]["role"] == "tool" and next_history[-1]["tool_name"] == "get_incident_scope"
    )
    assert "result" in json.loads(next_history[-1]["content"])
    assert diagnostic.export()["events"][-1]["support_check"] == "ADMITTED"


@pytest.mark.parametrize("count", [1, 2, 4])
def test_tool_and_explicit_final_phases_never_mix_tools_format_and_actual_offer(
    database, monkeypatch, count
):
    payloads = controlled(monkeypatch, count=count)
    report = run_agent(database, request(database))
    assert len(report.tool_trace) == count and report.ai_generated_selection
    for body in payloads:
        assert not ("tools" in body and "format" in body)
        assert body["stream"] is False and body["think"] is False
        if "format" in body:
            packet = json.loads(body["messages"][-1]["content"])
            assert (
                packet["response_schema"]
                == body["format"]
                == AgentFinalProposal.model_json_schema()
            )
            assert packet["task"] == "FINAL_CLAIM_IDS_ONLY"
            assert packet["executed_steps"] == list(range(1, count + 1))
            actual = {c["claim_id"] for c in packet["retrieved_claims"]}
            assert {c.claim_id for c in report.validated_claims} <= actual


def test_multistep_request_keeps_model_choice_and_reports_only_actual_executed_tool_count(
    database, monkeypatch
):
    payloads = controlled(monkeypatch, count=1)
    report = run_agent(database, request(database))
    initial = json.loads(payloads[0]["messages"][1]["content"])
    assert initial["requested_distinct_native_tools"] == 2
    tool = json.loads(next(m["content"] for m in payloads[1]["messages"] if m["role"] == "tool"))
    assert tool["distinct_tools_executed"] == 1 and tool["remaining_tool_calls"] == 3
    assert len(report.tool_trace) == 1 and report.tool_trace[0].selected_by == "LOCAL_MODEL"
    assert (
        report.ai_generated_selection
    )  # A valid single-tool result stays honest; no fake second step.


@pytest.mark.parametrize(
    "value",
    [
        [],
        None,
        "not-json",
        {"wrong": []},
        {"selected_claim_ids": None},
        {"selected_claim_ids": "wrong"},
        {"selected_claim_ids": ["C-" + "0" * 24] * 2},
        {"selected_claim_ids": ["C-" + "0" * 24] * 9},
        {"extra": PRIVATE},
        {"focus": None},
        {"abstain": "false"},
    ],
)
def test_final_structural_hypotheses_fail_closed_with_bounded_sanitized_diagnostics(
    database, monkeypatch, value
):
    def change(message, body):
        message["content"] = (
            json.dumps({**body, **value}) if isinstance(value, dict) else json.dumps(value)
        )
        return message

    controlled(monkeypatch, final_change=change)
    sink = StructuralDiagnostics()
    report = run_agent(database, request(database), diagnostics=sink)
    assert report.agent_status == "MODEL_OUTPUT_REJECTED" and not report.validated_claims
    assert report.rejection_codes == ["AGENT_FINISH_SCHEMA"]
    safe = json.dumps(sink.export())
    assert PRIVATE not in safe and "message.content" not in safe
    assert len(safe.encode()) <= 32768
    event = next(
        e for e in sink.export()["events"] if e["phase"] == "final_schema" and "json_parse" in e
    )
    assert "root_type" in event


def test_final_unknown_field_names_and_error_paths_never_escape_in_diagnostics(database):
    sink = StructuralDiagnostics()
    content = json.dumps({PRIVATE: PRIVATE, "selected_claim_ids": [{PRIVATE: PRIVATE}]})
    with pytest.raises(ToolError):
        admit_finish(context(database), [], content, diagnostics=sink)
    safe = json.dumps(sink.export())
    assert PRIVATE not in safe and "OTHER" in safe
    assert "input" not in safe and "ctx" not in safe


def test_actual_retrieved_but_unoffered_id_rejected_under_native_high_degree_cap(tmp_path):
    database = tmp_path / "fresh-cap.rl"
    seed_explanation_profile(database, "caps")
    c = create_context(database, "EV-CAPS", InvestigationOptions())
    steps = [
        execute_tool(c, name, {"subject": subject}, step_number=n + 1)
        for n, (name, subject) in enumerate(
            [
                ("get_incident_scope", "I000"),
                ("trace_deployment", "D000"),
                ("inspect_evidence", "E000"),
                ("inspect_gaps", "I000"),
            ]
        )
    ]
    offered = {v["claim_id"] for v in offered_claim_metadata(c, steps)}
    supported = retrieved_claims(c, steps)
    missing = next(v for v in supported if v.claim_id not in offered)
    ids = [missing.claim_id] + [v.claim_id for v in supported if v.claim_id != missing.claim_id][:2]
    with pytest.raises(ToolError) as e:
        admit_finish(
            c,
            steps,
            json.dumps(
                dict(
                    investigation_fingerprint=c.source_fingerprint,
                    selected_claim_ids=ids,
                    focus="BALANCED",
                    abstain=False,
                )
            ),
        )
    assert e.value.code == "CLAIM_NOT_OFFERED"


def test_final_tool_call_is_rejected_not_executed(database, monkeypatch):
    controlled(
        monkeypatch,
        final_change=lambda message, body: {
            **message,
            "tool_calls": [
                {"function": {"name": "inspect_evidence", "arguments": {"subject": "E000"}}}
            ],
        },
    )
    r = run_agent(database, request(database))
    assert len(r.tool_trace) == 2 and r.rejection_codes == ["AGENT_FINAL_TOOL_REJECTED"]
    assert not r.validated_claims


def test_pseudo_tool_content_is_never_executed(database, monkeypatch):
    controlled(
        monkeypatch,
        tool_message=lambda m: {
            "role": "assistant",
            "content": json.dumps(
                {"function": {"name": "get_incident_scope", "arguments": {"subject": "I000"}}}
            ),
        },
    )
    r = run_agent(database, request(database))
    assert r.tool_trace == [] and r.rejection_codes == ["AGENT_FINISH_SCHEMA"]


def test_non_utf8_provider_content_rejects_safely_instead_of_unhandled_exception(database):
    sink = StructuralDiagnostics()
    with pytest.raises(ToolError) as failure:
        admit_finish(context(database), [], "\ud800", diagnostics=sink)
    assert failure.value.code == "AGENT_FINISH_SCHEMA"
    assert "ud800" not in json.dumps(sink.export())


def test_zero_offered_supported_factual_claims_give_explicit_abstention(database, monkeypatch):
    controlled(monkeypatch, count=1)
    monkeypatch.setattr("traceweaver.agent.offered_claim_metadata", lambda *a: [])
    r = run_agent(database, request(database))
    assert r.agent_status == "ABSTAINED" and not r.ai_generated_selection
    assert all(c.claim_type == "NO_CAUSAL_VERDICT" for c in r.validated_claims)


@pytest.mark.parametrize(
    "code,unavailable,status",
    [
        ("OLLAMA_CONNECTION_UNAVAILABLE", True, "MODEL_UNAVAILABLE"),
        ("OLLAMA_TIMEOUT", False, "MODEL_OUTPUT_REJECTED"),
        ("OLLAMA_RESPONSE_JSON", False, "MODEL_OUTPUT_REJECTED"),
        ("OLLAMA_RESPONSE_LIMIT", False, "MODEL_OUTPUT_REJECTED"),
    ],
)
def test_transport_failures_remain_separate_safe_codes_not_schema_success(
    database, monkeypatch, code, unavailable, status
):
    controlled(monkeypatch, failure=OllamaFailure(code, unavailable=unavailable))
    sink = StructuralDiagnostics()
    r = run_agent(database, request(database), diagnostics=sink)
    assert r.agent_status == status and r.rejection_codes == [code] and not r.validated_claims
    assert any(e["phase"] == "transport" and e.get("code") == code for e in sink.export()["events"])


@pytest.mark.parametrize("failure", ["TIMEOUT", "CONNECTION_REFUSED", "CONNECTION_UNAVAILABLE"])
def test_probe_unavailable_stops_after_one_version_request_and_never_infers(monkeypatch, failure):
    calls = []

    def probe(route):
        calls.append(route)
        return None, failure

    monkeypatch.setattr("traceweaver.agent_diagnostics._probe_get", probe)
    result = probe_local_ollama()
    assert calls == ["/api/version"] and result["request_count"] == 1
    assert result["live_gate"] == "BLOCKED_DEPENDENCY" and result["failure_class"] == failure


def test_probe_requires_exact_installed_eligible_model_after_valid_version(monkeypatch):
    calls = []

    def probe(route):
        calls.append(route)
        return (
            {"version": "0.40.16"}
            if route == "/api/version"
            else {
                "models": [
                    {"name": "qwen3:8b", "size": 1, "remote_host": PRIVATE},
                    {"name": "other:1", "size": 1},
                ]
            },
            None,
        )

    monkeypatch.setattr("traceweaver.agent_diagnostics._probe_get", probe)
    r = probe_local_ollama()
    assert (
        len(calls) == 2
        and r["failure_class"] == "MODEL_NOT_INSTALLED"
        and PRIVATE not in json.dumps(r)
    )


def test_probe_reachable_exact_model_is_explicit_trial_permission_not_runtime_success(monkeypatch):
    monkeypatch.setattr(
        "traceweaver.agent_diagnostics._probe_get",
        lambda route: (
            {"version": "0.40.16"}
            if route == "/api/version"
            else {"models": [{"name": "qwen3:8b", "size": 1}]},
            None,
        ),
    )
    r = probe_local_ollama()
    assert r["live_gate"] == "AVAILABLE_FOR_EXPLICIT_TRIAL" and r["eligible_model_installed"]
    assert r["model_capabilities"] == "NOT_QUERIED"


def test_diagnostic_records_cap_and_unknown_runtime_fields_cannot_expose_prose():
    sink = StructuralDiagnostics()
    for _ in range(45):
        sink.response(
            {"done_reason": {PRIVATE: PRIVATE}, "message": {"content": "", "thinking": PRIVATE}},
            final=True,
        )
    r = sink.export()
    assert len(r["events"]) == 40 and r["events_dropped"] == 5 and PRIVATE not in json.dumps(r)
