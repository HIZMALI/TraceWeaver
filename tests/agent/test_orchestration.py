"""Controlled native-chat fixtures, never described as genuine live-model invocations."""

import json
import threading

import pytest

from traceweaver.agent import run_agent
from traceweaver.agent_models import AgentRequest, canonical_agent_payload
from traceweaver.agent_tools import ToolStore, create_context
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.ollama_local import OllamaFailure, OllamaLocal


def request(database, incident="INC-001"):
    c = create_context(database, incident, InvestigationOptions())
    return AgentRequest(
        incident_id=incident,
        options=c.options,
        source_fingerprint=c.source_fingerprint,
        intent="CHECK_COMPETING_DEPLOYMENTS",
        confirmed=True,
        model_id="controlled-unit:1",
    )


def scripted(monkeypatch, actions, finish=None, read_text=None):
    calls = []
    payloads = []

    def transport(self, method, route, payload=None, *, deadline=None):
        assert deadline is not None
        calls.append((method, route))
        payloads.append(payload)
        if route == "/api/tags":
            return {"models": [{"name": "controlled-unit:1", "size": 1}]}
        number = sum(r == "/api/chat" for _, r in calls) - 1
        if number < len(actions):
            value = actions[number]
            if isinstance(value, Exception):
                raise value
            if callable(value):
                value = value(payload)
            message = {"role": "assistant", "content": "", "tool_calls": value}
        else:
            source = json.loads(payload["messages"][1]["content"])
            last = next(
                (
                    json.loads(m["content"])
                    for m in reversed(payload["messages"])
                    if m["role"] == "tool"
                ),
                {},
            )
            ids = [c["claim_id"] for c in last.get("retrieved_claims", [])][:8]
            body = {
                "investigation_fingerprint": source["investigation_fingerprint"],
                "selected_claim_ids": ids,
                "focus": "BALANCED",
                "abstain": not ids,
            }
            if finish:
                body = finish(body, payload)
            message = {
                "role": "assistant",
                "content": read_text
                if read_text is not None and "format" not in payload
                else json.dumps(body),
            }
        return {"done": True, "model": "controlled-unit:1", "message": message}

    monkeypatch.setattr(OllamaLocal, "_request", transport)
    return calls, payloads


def call(name, subject):
    return [{"function": {"name": name, "arguments": {"subject": subject}}}]


def test_controlled_three_round_native_agent_returns_admitted_proof(database, monkeypatch):
    action = request(database)
    calls, payloads = scripted(
        monkeypatch, [call("get_incident_scope", "I000"), call("trace_deployment", "D001")]
    )
    before = database.read_bytes()
    report = run_agent(database, action)
    assert report.agent_status == "PARTIAL_CONTEXT"
    assert report.ai_directed_tools and report.ai_generated_selection
    assert [s.tool_name for s in report.tool_trace] == ["get_incident_scope", "trace_deployment"]
    assert report.model_interactions == 4 and len(calls) == 5
    assert report.validated_claims[-1].claim_type == "NO_CAUSAL_VERDICT"
    assert report.validated_citation_count == sum(len(c.citations) for c in report.validated_claims)
    assert database.read_bytes() == before
    packet = json.dumps(payloads)
    assert "INC-001" not in packet and "SVC-AUTH" not in packet and "source_ref" not in packet
    assert "N000" in packet and "retrieved_claims" in packet
    assert report.canonical_fingerprint and "elapsed_ms" not in json.dumps(
        canonical_agent_payload(report)
    )


def test_explicit_model_abstention_does_not_claim_ai_selected_factual_statements(
    database, monkeypatch
):
    scripted(
        monkeypatch,
        [call("get_incident_scope", "I000")],
        finish=lambda body, _: {**body, "selected_claim_ids": [], "abstain": True},
    )
    report = run_agent(database, request(database))
    assert report.agent_status == "ABSTAINED" and report.ai_directed_tools
    assert not report.ai_generated_selection
    assert [c.claim_type for c in report.validated_claims] == ["NO_CAUSAL_VERDICT"]


def test_native_readers_close_before_every_provider_round(database, monkeypatch):
    action = request(database)
    active = []
    threads = []
    enter, leave = ToolStore.__enter__, ToolStore.__exit__

    def observed_enter(self):
        active.append(self)
        threads.append(threading.get_ident())
        return enter(self)

    def observed_leave(self, *args):
        try:
            return leave(self, *args)
        finally:
            active.remove(self)
            threads.append(threading.get_ident())

    monkeypatch.setattr(ToolStore, "__enter__", observed_enter)
    monkeypatch.setattr(ToolStore, "__exit__", observed_leave)
    scripted(monkeypatch, [call("get_incident_scope", "I000")])
    transport = OllamaLocal._request

    def closed(*args, **kwargs):
        assert not active
        return transport(*args, **kwargs)

    monkeypatch.setattr(OllamaLocal, "_request", closed)
    report = run_agent(database, action)
    assert report.ai_directed_tools and len(set(threads)) == 1 and not active


@pytest.mark.parametrize(
    "actions,code",
    [
        ([call("write_cypher", "I000")], "AGENT_TOOL_REJECTED"),
        ([call("inspect_evidence", "E999")], "AGENT_SUBJECT_REJECTED"),
        (
            [
                [
                    {
                        "function": {
                            "name": "inspect_evidence",
                            "arguments": {"subject": "http://invalid"},
                        }
                    }
                ]
            ],
            "AGENT_ARGUMENT_SCHEMA",
        ),
        (
            [
                [
                    {
                        "function": {
                            "name": "inspect_evidence",
                            "arguments": {"subject": "E000", "cypher": "DELETE n"},
                        }
                    }
                ]
            ],
            "AGENT_ARGUMENT_SCHEMA",
        ),
        ([call("get_incident_scope", "I000") * 2], "AGENT_REPEATED_ACTION"),
        (
            [call("get_incident_scope", "I000"), call("get_incident_scope", "I000")],
            "AGENT_REPEATED_ACTION",
        ),
        (
            [
                [
                    {
                        "function": {
                            "name": "get_incident_scope",
                            "index": 1,
                            "arguments": {"subject": "I000"},
                        }
                    }
                ]
            ],
            "AGENT_CALL_SCHEMA",
        ),
        (
            [[{"function": {"name": "get_incident_scope", "arguments": '{"subject":"I000"}'}}]],
            "AGENT_ARGUMENT_SCHEMA",
        ),
    ],
)
def test_invalid_native_action_never_becomes_claims(database, monkeypatch, actions, code):
    action = request(database)
    scripted(monkeypatch, actions)
    before = database.read_bytes()
    report = run_agent(database, action)
    assert report.agent_status == "MODEL_OUTPUT_REJECTED" and code in report.rejection_codes
    assert not report.validated_claims and not report.ai_generated_selection
    assert database.read_bytes() == before


@pytest.mark.parametrize(
    "change,code",
    [
        (
            lambda b, p: {**b, "selected_claim_ids": ["C-" + "0" * 24], "abstain": False},
            "UNKNOWN_CLAIM_ID",
        ),
        (lambda b, p: {**b, "facts": "The deployment caused the incident"}, "AGENT_FINISH_SCHEMA"),
        (lambda b, p: {**b, "causal_conclusion": "ESTABLISHED"}, "AGENT_FINISH_SCHEMA"),
        (lambda b, p: {**b, "investigation_fingerprint": "0" * 64}, "SNAPSHOT_MISMATCH"),
        (lambda b, p: {**b, "tool_steps": [4]}, "AGENT_UNKNOWN_STEP"),
        (lambda b, p: {**b, "tool_steps": [1, 1]}, "AGENT_UNKNOWN_STEP"),
        (lambda b, p: {**b, "focus": "BLAME_DEPLOYMENT"}, "AGENT_FINISH_SCHEMA"),
    ],
)
def test_final_proposal_firewall_rejects_invalid_selections(database, monkeypatch, change, code):
    action = request(database)
    scripted(monkeypatch, [call("get_incident_scope", "I000")], finish=change)
    r = run_agent(database, action)
    assert code in r.rejection_codes and not r.validated_claims
    assert (
        r.causal_conclusion == "NOT_ESTABLISHED"
        and r.external_verification_status == "NOT_PERFORMED"
    )
    assert r.ai_directed_tools and not r.ai_generated_selection


def test_source_admissible_but_unretrieved_claim_is_rejected(database, monkeypatch):
    action = request(database)
    c = create_context(database, "INC-001", action.options)
    claim = next(x for x in c.catalog.claims if x.claim_type == "DEPLOYMENT_CONNECTED")
    scripted(
        monkeypatch,
        [call("get_incident_scope", "I000")],
        finish=lambda b, p: {**b, "selected_claim_ids": [claim.claim_id], "abstain": False},
    )
    r = run_agent(database, action)
    assert r.rejection_codes == ["CLAIM_NOT_RETRIEVED"]


def test_no_tool_call_is_selection_only_not_ai_tool_evidence(database, monkeypatch):
    action = request(database)
    scripted(monkeypatch, [])
    r = run_agent(database, action)
    assert r.agent_status == "MODEL_SELECTION_ONLY" and not r.tool_trace
    assert not r.ai_directed_tools and not r.ai_generated_selection


def test_four_calls_and_five_model_interactions_are_hard_bounds(database, monkeypatch):
    action = request(database)
    actions = [
        call("get_incident_scope", "I000"),
        call("trace_deployment", "D000"),
        call("trace_deployment", "D001"),
        call("inspect_evidence", "E000"),
        call("inspect_evidence", "E001"),
    ]
    calls, _ = scripted(monkeypatch, actions)
    r = run_agent(database, action)
    assert r.agent_status == "BUDGET_EXHAUSTED" and r.rejection_codes == ["AGENT_TOOL_BUDGET"]
    assert len(r.tool_trace) == 4 and r.model_interactions == 5 and len(calls) == 6
    assert not r.validated_claims


def test_total_deadline_prevents_provider_request(database, monkeypatch):
    action = request(database)
    calls, _ = scripted(monkeypatch, [])
    monkeypatch.setattr("traceweaver.agent.TOTAL_SECONDS", -1)
    r = run_agent(database, action)
    assert r.agent_status == "BUDGET_EXHAUSTED" and not calls


def test_valid_parallel_batch_executes_only_first_with_explicit_warning(database, monkeypatch):
    action = request(database)
    scripted(monkeypatch, [call("get_incident_scope", "I000") + call("trace_deployment", "D001")])
    r = run_agent(database, action)
    assert len(r.tool_trace) == 1 and r.tool_trace[0].tool_name == "get_incident_scope"
    assert r.tool_trace[0].deferred_proposal_count == 1
    assert r.proposal_warnings == ["PARALLEL_PROPOSALS_CONSTRAINED", "READ_PHASE_TEXT_NOT_USED"]
    assert r.native_query_count == 10
    assert not any(c.claim_type.startswith("DEPLOYMENT") for c in r.validated_claims)


def test_invalid_tail_of_batch_aborts_every_call_before_native_execution(database, monkeypatch):
    action = request(database)
    scripted(monkeypatch, [call("get_incident_scope", "I000") + call("write_cypher", "I000")])
    r = run_agent(database, action)
    assert r.agent_status == "MODEL_OUTPUT_REJECTED" and not r.tool_trace
    assert r.native_query_count == 7 and r.rejection_codes == ["AGENT_TOOL_REJECTED"]


def test_read_phase_prose_is_discarded_not_echoed_or_accepted_as_final_facts(database, monkeypatch):
    action = request(database)
    hostile = "SYNTHETIC UNTRUSTED ROOT CAUSE http://invalid/private"
    _, payloads = scripted(monkeypatch, [call("get_incident_scope", "I000")], read_text=hostile)
    r = run_agent(database, action)
    assert r.validated_claims and r.proposal_warnings == ["READ_PHASE_TEXT_NOT_USED"]
    assert hostile not in json.dumps(payloads) and hostile not in r.model_dump_json()
    assert r.model_interactions == 3 and r.causal_conclusion == "NOT_ESTABLISHED"


@pytest.mark.parametrize(
    "failure,status",
    [
        (OllamaFailure("OLLAMA_TIMEOUT"), "MODEL_OUTPUT_REJECTED"),
        (OllamaFailure("OLLAMA_CONNECTION_UNAVAILABLE", unavailable=True), "MODEL_UNAVAILABLE"),
    ],
)
def test_provider_failure_keeps_actual_trace_but_no_fallback_claims(
    database, monkeypatch, failure, status
):
    action = request(database)
    scripted(monkeypatch, [call("get_incident_scope", "I000"), failure])
    r = run_agent(database, action)
    assert r.agent_status == status and len(r.tool_trace) == 1 and not r.validated_claims
    assert not r.ai_generated_selection


def test_source_changed_while_model_running_aborts_before_native_tool(database, monkeypatch):
    from traceweaver.storage import GraphStore

    action = request(database)

    def changed(payload):
        with GraphStore(database, read_only=False) as store:
            store.execute(
                "MATCH (i:Incident {id:$id}) SET i.title=$title",
                {"id": "INC-001", "title": "Synthetic change during provider"},
            )
        return call("get_incident_scope", "I000")

    scripted(monkeypatch, [changed])
    r = run_agent(database, action)
    assert r.agent_status == "STALE_SNAPSHOT" and not r.tool_trace and not r.validated_claims
