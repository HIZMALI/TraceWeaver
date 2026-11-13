"""Controlled provider protocol cases; native graph remains real in every selection test."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.dashboard import dashboard
from traceweaver.ollama_local import OllamaFailure
from traceweaver.storage import GraphStore

BASE = "http://127.0.0.1:8000"


@pytest.fixture
def local_client(database):
    with TestClient(
        create_app(Settings(database=database)), base_url=BASE, client=("127.0.0.1", 42000)
    ) as client:
        yield client


def action(database):
    b = dashboard(database, "INC-001")
    return {
        "incident_id": "INC-001",
        "options": b.investigation.options.model_dump(),
        "source_fingerprint": b.source_fingerprint,
        "model_id": "unit-local:1",
        "confirmed": True,
    }


def provider(monkeypatch, mode="valid"):
    calls = []

    def request(self, method, route, payload=None):
        calls.append((method, route))
        if route == "/api/tags":
            return {
                "models": [
                    {"name": "unit-local:1", "size": 123},
                    {"name": "bad-cloud:1", "size": 50},
                    {"name": "bad-remote:1", "size": 50, "remote_host": "invalid"},
                ]
            }
        packet = json.loads(payload["messages"][1]["content"])
        assert "INC-001" not in json.dumps(payload)
        assert "source_ref" not in json.dumps(packet)
        ids = [c["claim_id"] for c in packet["claims"][:3]]
        if mode == "unknown":
            ids[0] = "C-" + "0" * 24
        if mode == "timeout":
            raise OllamaFailure("OLLAMA_TIMEOUT")
        result = {
            "investigation_fingerprint": packet["investigation_fingerprint"],
            "selected_claim_ids": ids,
            "focus": "BALANCED",
            "abstain": False,
        }
        if mode == "prose":
            result["facts"] = "Untrusted provider prose"
        return {
            "done": True,
            "model": "unit-local:1",
            "message": {"role": "assistant", "content": json.dumps(result)},
        }

    monkeypatch.setattr("traceweaver.ollama_local.OllamaLocal._request", request)
    return calls


@pytest.mark.parametrize(
    "origin",
    [None, "null", "http://evil.example", "http://localhost:8000", "http://127.0.0.1:8001"],
)
def test_post_requires_exact_origin_before_provider(local_client, monkeypatch, origin):
    calls = provider(monkeypatch)
    r = local_client.post(
        "/console/models/capabilities",
        json={"action": "LIST_INSTALLED_MODELS"},
        headers={} if origin is None else {"origin": origin},
    )
    assert r.status_code == 403 and calls == []


@pytest.mark.parametrize(
    "content_type",
    ["text/plain", "application/x-www-form-urlencoded", "application/json; charset=latin1"],
)
def test_post_requires_exact_json(local_client, monkeypatch, content_type):
    calls = provider(monkeypatch)
    r = local_client.post(
        "/console/models/capabilities",
        content="{}",
        headers={"origin": BASE, "content-type": content_type},
    )
    assert r.status_code == 415 and not calls


@pytest.mark.parametrize(
    "body",
    [
        '{"action":"LIST_INSTALLED_MODELS","prompt":"private"}',
        '{"action":"LIST_INSTALLED_MODELS","action":"other"}',
        "[" * 8 + "0" + "]" * 8,
        "not json",
    ],
)
def test_bounded_strict_action_rejects_untrusted_body(local_client, monkeypatch, body):
    calls = provider(monkeypatch)
    r = local_client.post(
        "/console/models/capabilities",
        content=body,
        headers={"origin": BASE, "content-type": "application/json"},
    )
    assert r.status_code == 422 and not calls
    assert "private" not in r.text


def test_post_size_rejected_before_provider(local_client, monkeypatch):
    calls = provider(monkeypatch)
    r = local_client.post(
        "/console/models/capabilities",
        content="x" * 2049,
        headers={"origin": BASE, "content-type": "application/json"},
    )
    assert r.status_code == 413 and not calls


def test_malformed_excessive_length_header_is_bounded_before_integer_parse(
    local_client, monkeypatch
):
    calls = provider(monkeypatch)
    response = local_client.post(
        "/console/models/capabilities",
        content="{}",
        headers={"origin": BASE, "content-type": "application/json", "content-length": "9" * 5000},
    )
    assert response.status_code == 413 and not calls


def test_capabilities_only_admit_eligible_installed_tags(local_client, monkeypatch):
    calls = provider(monkeypatch)
    r = local_client.post(
        "/console/models/capabilities",
        json={"action": "LIST_INSTALLED_MODELS"},
        headers={"origin": BASE},
    )
    assert r.status_code == 200 and r.json()["models"] == ["unit-local:1"]
    assert calls == [("GET", "/api/tags")]


@pytest.mark.parametrize(
    "mode,expected",
    [("valid", "OLLAMA"), ("unknown", "NONE"), ("prose", "NONE"), ("timeout", "NONE")],
)
def test_native_selection_firewall_modes_and_immutable_store(
    local_client, database, monkeypatch, mode, expected
):
    calls = provider(monkeypatch, mode)
    before = database.read_bytes()
    r = local_client.post("/console/selection", json=action(database), headers={"origin": BASE})
    assert r.status_code == 200
    e = r.json()["explanation"]
    assert e["mode_executed"] == expected
    assert e["ai_generated_selection"] == (expected == "OLLAMA")
    assert e["causal_conclusion"] == "NOT_ESTABLISHED"
    assert (len(e["claims"]) > 0) == (expected == "OLLAMA")
    assert "Untrusted provider prose" not in r.text
    assert calls == [("GET", "/api/tags"), ("POST", "/api/chat")]
    assert database.read_bytes() == before


def test_changed_native_snapshot_rejected_before_provider(local_client, database, monkeypatch):
    calls = provider(monkeypatch)
    body = action(database)
    body["source_fingerprint"] = "0" * 64
    assert (
        local_client.post("/console/selection", json=body, headers={"origin": BASE}).status_code
        == 409
    )
    assert not calls


@pytest.mark.parametrize(
    "field,value",
    [
        ("confirmed", False),
        ("confirmed", 1),
        ("model_id", "http://evil.example"),
        ("model_id", "cloud-model:1"),
        ("prompt", "secret"),
        ("host", "evil.example"),
    ],
)
def test_selection_payload_is_allowlisted(local_client, database, monkeypatch, field, value):
    calls = provider(monkeypatch)
    body = action(database)
    body[field] = value
    assert (
        local_client.post("/console/selection", json=body, headers={"origin": BASE}).status_code
        == 422
    )
    assert not calls


def test_one_inflight_action_rejects_duplicate_without_provider_flood(local_client, monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def blocked(self, *args):
        entered.set()
        assert release.wait(5)
        return {"models": []}

    monkeypatch.setattr("traceweaver.ollama_local.OllamaLocal._request", blocked)
    with ThreadPoolExecutor(max_workers=1) as worker:
        future = worker.submit(
            local_client.post,
            "/console/models/capabilities",
            json={"action": "LIST_INSTALLED_MODELS"},
            headers={"origin": BASE},
        )
        try:
            assert entered.wait(3)
            assert (
                local_client.post(
                    "/console/models/capabilities",
                    json={"action": "LIST_INSTALLED_MODELS"},
                    headers={"origin": BASE},
                ).status_code
                == 429
            )
        finally:
            release.set()
        assert future.result().status_code == 200


def test_capability_unavailable_is_honest(local_client, monkeypatch):
    def unavailable(*args):
        raise OllamaFailure("OLLAMA_CONNECTION_UNAVAILABLE", unavailable=True)

    monkeypatch.setattr("traceweaver.ollama_local.OllamaLocal._request", unavailable)
    r = local_client.post(
        "/console/models/capabilities",
        json={"action": "LIST_INSTALLED_MODELS"},
        headers={"origin": BASE},
    )
    assert r.json() == {
        "models": [],
        "truncated": False,
        "status": "UNAVAILABLE",
        "code": "OLLAMA_CONNECTION_UNAVAILABLE",
    }


def test_new_action_gets_never_call_provider(local_client, monkeypatch):
    calls = provider(monkeypatch)
    assert local_client.get("/console/models/capabilities").status_code == 405
    assert local_client.get("/console/selection?mode=ollama").status_code == 405
    assert not calls


def test_openapi_documents_exact_bounded_action_models(local_client):
    paths = local_client.get("/openapi.json").json()["paths"]
    action = paths["/console/selection"]["post"]["requestBody"]["content"]["application/json"][
        "schema"
    ]
    assert action["additionalProperties"] is False
    assert set(action["required"]) == {
        "incident_id",
        "options",
        "source_fingerprint",
        "model_id",
        "confirmed",
    }
    assert action["properties"]["confirmed"]["const"] is True
    assert action["properties"]["options"]["properties"]["pre_minutes"]["maximum"] == 1440
    assert "$defs" not in json.dumps(action) and "$ref" not in json.dumps(action)


def test_worker_reader_closes_before_any_provider_request(local_client, database, monkeypatch):
    events = []

    class Observed(GraphStore):
        def __enter__(self):
            events.append(("open", threading.get_ident()))
            assert self.read_only
            return super().__enter__()

        def __exit__(self, *args):
            result = super().__exit__(*args)
            events.append(("closed", threading.get_ident()))
            return result

    body = action(database)
    monkeypatch.setattr("traceweaver.console_selection.GraphStore", Observed)

    def tags(self, *args):
        assert [event[0] for event in events] == ["open", "closed"]
        assert len({event[1] for event in events}) == 1
        assert threading.get_ident() == events[0][1]
        return {"models": []}

    monkeypatch.setattr("traceweaver.ollama_local.OllamaLocal._request", tags)
    response = local_client.post("/console/selection", json=body, headers={"origin": BASE})
    assert response.status_code == 200
    assert response.json()["explanation"]["explanation_status"] == "MODEL_UNAVAILABLE"
