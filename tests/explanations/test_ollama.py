"""Controlled local protocol tests. None of these fixtures is real LLM inference."""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from traceweaver.citation_validator import CitationRejected
from traceweaver.explanation import explain
from traceweaver.explanation_catalog import build_catalog
from traceweaver.model_selection import accept_proposal, sanitized_packet
from traceweaver.ollama_local import OllamaFailure, OllamaLocal

MODEL = "test-model:1"


@pytest.fixture
def local_transport(monkeypatch):
    state = {
        "requests": [],
        "transform": None,
        "delay": 0,
        "status": 200,
        "content_type": "application/json",
        "raw": None,
        "omit_length": False,
    }

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def do_GET(self):
            self.respond()

        def do_POST(self):
            self.respond()

        def respond(self):
            size = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(size)) if size else None
            state["requests"].append((self.command, self.path, payload, dict(self.headers)))
            if state["delay"]:
                time.sleep(state["delay"])
            if self.path == "/api/tags":
                data = {"models": [{"name": MODEL, "size": 1024}]}
            else:
                packet = json.loads(payload["messages"][1]["content"])
                proposal = {
                    "investigation_fingerprint": packet["investigation_fingerprint"],
                    "selected_claim_ids": [c["claim_id"] for c in packet["claims"][:3]],
                    "focus": "BALANCED",
                    "abstain": False,
                }
                data = {
                    "model": MODEL,
                    "done": True,
                    "done_reason": "stop",
                    "message": {"role": "assistant", "content": json.dumps(proposal)},
                }
            if state["transform"]:
                data = state["transform"](self.path, data)
            raw = state["raw"] if state["raw"] is not None else json.dumps(data).encode()
            self.send_response(state["status"])
            self.send_header("Content-Type", state["content_type"])
            self.send_header("Connection", "close")
            self.close_connection = True
            self.send_header("Location", "http://synthetic-external.invalid/must-not-follow")
            if not state["omit_length"]:
                self.send_header("Content-Length", str(len(raw)))
            else:
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    monkeypatch.setattr("traceweaver.ollama_local.PORT", server.server_port)
    thread.start()
    yield state
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_native_structured_protocol_accepted_with_real_graph_and_no_proxies(
    database, local_transport, monkeypatch
):
    monkeypatch.setenv("HTTP_PROXY", "http://synthetic-external.invalid:9999")
    monkeypatch.setenv("ALL_PROXY", "http://synthetic-external.invalid:9999")
    original = socket.getaddrinfo

    def only_loopback(host, *args, **kwargs):
        assert host == "127.0.0.1"
        return original(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", only_loopback)
    before = database.read_bytes()
    report = explain(database, "INC-001", mode="ollama", model=MODEL)
    assert report.mode_executed == "OLLAMA" and report.ai_generated_selection
    assert report.model.model_id == MODEL and not report.rejection_codes
    assert report.claims[-1].claim_type == "NO_CAUSAL_VERDICT"
    assert [(m, p) for m, p, _, _ in local_transport["requests"]] == [
        ("GET", "/api/tags"),
        ("POST", "/api/chat"),
    ]
    payload = local_transport["requests"][1][2]
    assert payload["stream"] is False and payload["think"] is False
    assert payload["format"]["additionalProperties"] is False
    assert payload["options"]["temperature"] == 0
    assert payload["options"]["num_predict"] == 512
    assert "tools" not in payload
    for _, _, _, headers in local_transport["requests"]:
        assert "Authorization" not in headers and "Proxy-Authorization" not in headers
    packet = payload["messages"][1]["content"]
    assert "INC-001" not in packet and "EVD-001" not in packet and "demo://" not in packet
    assert database.read_bytes() == before


@pytest.mark.parametrize(
    "attack", ["malformed", "partial", "redirect", "oversized", "stream_type", "timeout"]
)
def test_transport_failures_are_explicit_without_fallback(
    database, local_transport, monkeypatch, attack
):
    if attack == "malformed":
        local_transport["raw"] = b"not json"
    if attack == "partial":
        local_transport["raw"] = b'{"models":'
    if attack == "redirect":
        local_transport["status"] = 302
    if attack == "oversized":
        local_transport["raw"] = b"x" * 65537
    if attack == "stream_type":
        local_transport["content_type"] = "application/x-ndjson"
    if attack == "timeout":
        local_transport["delay"] = 0.15
        monkeypatch.setattr("traceweaver.ollama_local.READ_TIMEOUT", 0.03)
        monkeypatch.setattr("traceweaver.ollama_local.TOTAL_TIMEOUT", 0.05)
    report = explain(database, "INC-001", mode="ollama", model=MODEL)
    assert report.explanation_status == "MODEL_OUTPUT_REJECTED"
    assert report.mode_executed == "NONE" and not report.ai_generated_selection
    assert report.claims == [] and report.model is None
    assert len(local_transport["requests"]) == 1  # No redirect/retry/pull route.


def test_undeclared_oversize_body_is_bounded(baseline_context, local_transport):
    local_transport["raw"] = b"x" * 65537
    local_transport["omit_length"] = True
    with pytest.raises(OllamaFailure) as error:
        OllamaLocal().select(build_catalog(baseline_context), MODEL)
    assert error.value.code == "OLLAMA_RESPONSE_LIMIT"


@pytest.mark.parametrize(
    "attack", ["role", "extra_tool", "not_done", "wrong_model", "token_limit", "bad_content"]
)
def test_native_chat_envelope_fails_closed(database, local_transport, attack):
    def transform(route, data):
        if route == "/api/tags":
            return data
        if attack == "role":
            data["message"]["role"] = "user"
        if attack == "extra_tool":
            data["message"]["tool_calls"] = [{"name": "execute"}]
        if attack == "not_done":
            data["done"] = False
        if attack == "wrong_model":
            data["model"] = "invented-model:1"
        if attack == "token_limit":
            data["done_reason"] = "length"
        if attack == "bad_content":
            data["message"]["content"] = {"claims": []}
        return data

    local_transport["transform"] = transform
    report = explain(database, "INC-001", mode="ollama", model=MODEL)
    assert report.explanation_status == "MODEL_OUTPUT_REJECTED"
    assert report.rejection_codes == ["OLLAMA_CHAT_SCHEMA"]


@pytest.mark.parametrize(
    "model", [None, "", "../model", "https://remote.invalid/model", "qwen-cloud:1", "x" * 129]
)
def test_invalid_or_cloud_model_is_rejected_before_network(
    baseline_context, local_transport, model
):
    with pytest.raises(OllamaFailure) as error:
        OllamaLocal().select(build_catalog(baseline_context), model)
    assert error.value.unavailable
    assert local_transport["requests"] == []


def test_uninstalled_model_never_triggers_download(database, local_transport):
    report = explain(database, "INC-001", mode="ollama", model="missing-model:1")
    assert report.explanation_status == "MODEL_UNAVAILABLE"
    assert [(m, p) for m, p, _, _ in local_transport["requests"]] == [("GET", "/api/tags")]


@pytest.mark.parametrize(
    "attack",
    [
        "unknown",
        "snapshot",
        "duplicate",
        "excessive",
        "extra",
        "cypher",
        "source_url",
        "truth",
        "nested",
        "oversize",
        "fenced",
        "bool_string",
    ],
)
def test_untrusted_selector_content_is_rejected(scenario_context, scenario_catalog, attack):
    ids = [c.claim_id for c in scenario_catalog.claims[:3]]
    proposal = {
        "investigation_fingerprint": scenario_catalog.investigation_fingerprint,
        "selected_claim_ids": ids,
        "focus": "BALANCED",
        "abstain": False,
    }
    if attack == "unknown":
        proposal["selected_claim_ids"][0] = "C-" + "0" * 24
    if attack == "snapshot":
        proposal["investigation_fingerprint"] = "0" * 64
    if attack == "duplicate":
        proposal["selected_claim_ids"] = [ids[0]] * 3
    if attack == "excessive":
        proposal["selected_claim_ids"] = [c.claim_id for c in scenario_catalog.claims[:9]]
    if attack == "extra":
        proposal["statement"] = "confirmed root cause"
    if attack == "cypher":
        proposal["cypher"] = "MATCH (n) DELETE n"
    if attack == "source_url":
        proposal["source_ref"] = "https://invented.invalid"
    if attack == "truth":
        proposal["causal_conclusion"] = "ESTABLISHED"
    if attack == "nested":
        proposal["selected_claim_ids"] = [[[[[[[]]]]]]]
    if attack == "bool_string":
        proposal["abstain"] = "false"
    raw = json.dumps(proposal).encode()
    if attack == "oversize":
        raw += b" " * 4097
    if attack == "fenced":
        raw = b"```json\n" + raw + b"\n```"
    with pytest.raises(CitationRejected):
        accept_proposal(raw, scenario_context, scenario_catalog)


def test_accepted_abstention_only_renders_caution(scenario_context, scenario_catalog):
    raw = json.dumps(
        {
            "investigation_fingerprint": scenario_catalog.investigation_fingerprint,
            "selected_claim_ids": [],
            "focus": "GAPS",
            "abstain": True,
        }
    ).encode()
    claims, abstain = accept_proposal(raw, scenario_context, scenario_catalog)
    assert abstain and [c.claim_type for c in claims] == ["NO_CAUSAL_VERDICT"]


def test_provider_order_is_preserved_with_mandatory_final_caution(
    scenario_context, scenario_catalog
):
    ids = [c.claim_id for c in scenario_catalog.claims[:3]][::-1]
    raw = json.dumps(
        {
            "investigation_fingerprint": scenario_catalog.investigation_fingerprint,
            "selected_claim_ids": ids,
            "focus": "TIMELINE",
            "abstain": False,
        }
    ).encode()
    claims, _ = accept_proposal(raw, scenario_context, scenario_catalog)
    assert [c.claim_id for c in claims if c.claim_type != "NO_CAUSAL_VERDICT"] == [
        value for value in ids if value != scenario_catalog.claims[0].claim_id
    ]
    assert claims[-1].claim_type == "NO_CAUSAL_VERDICT"


def test_response_unknown_claim_produces_rejected_report(database, local_transport):
    def transform(route, data):
        if route == "/api/chat":
            content = json.loads(data["message"]["content"])
            content["selected_claim_ids"][0] = "C-" + "0" * 24
            data["message"]["content"] = json.dumps(content)
        return data

    local_transport["transform"] = transform
    before = database.read_bytes()
    report = explain(database, "INC-001", mode="ollama", model=MODEL)
    assert report.explanation_status == "MODEL_OUTPUT_REJECTED"
    assert report.rejection_codes == ["UNKNOWN_CLAIM_ID"] and report.claims == []
    assert database.read_bytes() == before


def test_connection_refusal_is_unavailable(database, monkeypatch):
    connection = socket.socket()
    connection.bind(("127.0.0.1", 0))
    port = connection.getsockname()[1]
    connection.close()
    monkeypatch.setattr("traceweaver.ollama_local.PORT", port)
    report = explain(database, "INC-001", mode="ollama", model=MODEL)
    assert report.explanation_status == "MODEL_UNAVAILABLE" and report.mode_executed == "NONE"


def test_routes_are_allowlisted_before_socket_open():
    with pytest.raises(OllamaFailure) as error:
        OllamaLocal()._request("GET", "http://synthetic-external.invalid/")
    assert error.value.code == "OLLAMA_ROUTE_REJECTED"


def test_prompt_packet_has_no_unbounded_graph_payload(scenario_catalog):
    packet = sanitized_packet(scenario_catalog)
    assert len(json.dumps(packet).encode()) <= 32768
    assert set(packet) == {"investigation_fingerprint", "task", "claims"}
    assert all(
        set(c)
        == {
            "claim_id",
            "claim_type",
            "citation_kinds",
            "temporal_classification",
            "verification_status",
        }
        for c in packet["claims"]
    )


def test_request_byte_limit_rejects_before_connection(local_transport):
    with pytest.raises(OllamaFailure) as error:
        OllamaLocal()._request("POST", "/api/chat", {"synthetic": "x" * 49153})
    assert error.value.code == "OLLAMA_REQUEST_LIMIT"
    assert local_transport["requests"] == []
