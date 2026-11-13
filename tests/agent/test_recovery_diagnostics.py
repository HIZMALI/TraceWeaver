"""CONTROLLED fixed-local probe transport shapes; no real daemon/model inference."""

import http.client
import json

import pytest

from traceweaver.agent_diagnostics import StructuralDiagnostics, _probe_get, probe_local_ollama
from traceweaver.agent_provider import AgentFinalProposal
from traceweaver.tool_errors import ToolError


@pytest.mark.parametrize(
    "scenario,code",
    [
        ("valid", None),
        ("status", "HTTP_STATUS"),
        ("type", "RESPONSE_TYPE"),
        ("length", "RESPONSE_LIMIT"),
        ("oversize", "RESPONSE_LIMIT"),
        ("json", "RESPONSE_JSON"),
        ("root", "RESPONSE_JSON"),
        ("refused", "CONNECTION_REFUSED"),
        ("timeout", "TIMEOUT"),
        ("broken", "CONNECTION_UNAVAILABLE"),
    ],
)
def test_probe_fixed_origin_route_deadline_byte_cap_and_safe_failure(monkeypatch, scenario, code):
    events = []

    class Response:
        status = 503 if scenario == "status" else 200

        def getheader(self, key, default=None):
            return {
                "Content-Type": "text/plain" if scenario == "type" else "application/json",
                "Content-Length": "65537" if scenario == "length" else None,
            }.get(key, default)

        def read(self, size):
            events.append(("read", size))
            return (
                b"x" * 65537
                if scenario == "oversize"
                else b"not-json"
                if scenario == "json"
                else b"[]"
                if scenario == "root"
                else b'{"version":"0.40.16"}'
            )

    class Connection:
        sock = object()

        def __init__(self, host, port, timeout):
            events.append((host, port, timeout))

        def connect(self):
            if scenario == "refused":
                raise ConnectionRefusedError("SYNTHETIC_PRIVATE")
            if scenario == "timeout":
                raise TimeoutError("SYNTHETIC_PRIVATE")

        def request(self, method, route):
            events.append((method, route))
            if scenario == "broken":
                raise http.client.HTTPException("SYNTHETIC_PRIVATE")

        def getresponse(self):
            return Response()

        def close(self):
            events.append("closed")

    monkeypatch.setattr("traceweaver.agent_diagnostics.http.client.HTTPConnection", Connection)
    value, actual = _probe_get("/api/version")
    assert actual == code and events[0] == ("127.0.0.1", 11434, 2) and events[-1] == "closed"
    assert "SYNTHETIC_PRIVATE" not in json.dumps([value, actual])
    if actual is None:
        assert value["version"] == "0.40.16"
    if ("GET", "/api/version") in events:
        assert not any("POST" in str(x) for x in events)


def test_probe_cannot_accept_show_pull_or_arbitrary_endpoint():
    for route in ("/api/pull", "/api/chat", "http://other.invalid/api/version"):
        with pytest.raises(ToolError) as failure:
            _probe_get(route)
        assert failure.value.code == "DIAGNOSTIC_ROUTE_REJECTED"


@pytest.mark.parametrize(
    "version", [None, "SYNTHETIC_PRIVATE\nhttp://invalid", {"private": "value"}]
)
def test_probe_invalid_version_cannot_escape_or_trigger_second_request(monkeypatch, version):
    calls = []

    def get(route):
        calls.append(route)
        return {"version": version}, None

    monkeypatch.setattr("traceweaver.agent_diagnostics._probe_get", get)
    r = probe_local_ollama()
    assert calls == ["/api/version"] and r["reachable"]
    assert r["failure_class"] == "VERSION_SCHEMA" and "SYNTHETIC_PRIVATE" not in json.dumps(r)


def test_diagnostics_schema_failure_and_valid_supported_object_are_distinct_without_values():
    sink = StructuralDiagnostics()
    sink.finish('{"selected_claim_ids":null}', AgentFinalProposal)
    sink.finish(
        json.dumps(
            dict(
                investigation_fingerprint="0" * 64,
                selected_claim_ids=[],
                abstain=True,
                focus="BALANCED",
            )
        ),
        AgentFinalProposal,
    )
    first, second = sink.export()["events"]
    assert first["schema_valid"] is False and second["schema_valid"] is True
    assert {v["type"] for v in first["errors"]} >= {"missing", "list_type"}
    assert "0" * 64 not in json.dumps(sink.export())


def test_diagnostics_export_owns_nested_data_instead_of_exposing_mutable_record_list():
    sink = StructuralDiagnostics()
    sink.failure("transport", "OLLAMA_TIMEOUT")
    copy = sink.export()
    copy["events"].clear()
    assert len(sink.export()["events"]) == 1


def test_duplicate_json_is_diagnosed_as_strict_parse_rejection_never_normalized():
    sink = StructuralDiagnostics()
    sink.finish('{"abstain":true,"abstain":false}', AgentFinalProposal)
    event = sink.export()["events"][0]
    assert event["json_parse"] == "PARSED" and event["strict_object_parse"] == "REJECTED"
    assert event["strict_parse_code"] == "DUPLICATE_JSON_KEY" and "schema_valid" not in event
