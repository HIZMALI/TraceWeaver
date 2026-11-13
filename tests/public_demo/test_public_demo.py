"""Native public surface checks; test assets exercise serving, not simulated graph responses."""

import hashlib
import shutil
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from traceweaver import public_demo, public_server
from traceweaver.public_demo import PublicSettings, create_app
from traceweaver.storage import GraphStore

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def public_setup(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "examples/judge-demo", bundle)
    assets = tmp_path / "public-assets"
    (assets / "assets").mkdir(parents=True)
    (assets / "index.html").write_text(
        '<html><head><meta name="traceweaver-mode" content="public">'
        '<link href="/assets/index-test.css" rel="stylesheet"></head>'
        '<body><script src="/assets/index-test.js"></script></body></html>',
        encoding="utf8",
    )
    for name in ("index-test.js", "index-test.css", "third-party-licenses.txt"):
        (assets / "assets" / name).write_text("/* controlled serving fixture */", encoding="utf8")
    return PublicSettings(bundle, ("demo.test",), assets)


@pytest.fixture
def public_client(public_setup):
    with TestClient(create_app(public_setup), base_url="https://demo.test") as client:
        yield client


def test_native_startup_incidents_paths_citations_and_byte_preservation(
    public_client, public_setup
):
    database = public_setup.bundle / "traceweaver-demo.rl"
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    health = public_client.get("/health")
    assert health.json() == {
        "status": "ok",
        "database_engine": "relate",
        "synthetic": True,
        "read_only": True,
    }
    rows = public_client.get("/console/incidents").json()["incidents"]
    assert {row["id"] for row in rows} == {
        "INC-001",
        "INC-002",
        "CASE-INC",
        "CASE-NO-TIME",
        "CASE-OTHER",
    }
    response = public_client.get("/incidents/INC-001/dashboard")
    assert response.status_code == 200
    payload = response.json()
    investigation = payload["investigation"]
    assert len(investigation["evidence"]) == 4
    assert len(payload["explanation"]["claims"]) == 8
    assert sum(len(c["citations"]) for c in payload["explanation"]["claims"]) == 11
    assert investigation["causal_conclusion"] == "NOT_ESTABLISHED"
    candidates = investigation["candidates"]
    assert {(c["deployment_id"], c["target_service_id"]) for c in candidates} == {
        ("DEP-001", "SVC-AUTH"),
        ("DEP-002", "SVC-PAYMENT"),
    }
    auth = next(c for c in candidates if c["deployment_id"] == "DEP-001")
    path = auth["graph_paths"][0]
    assert path["node_ids"] == ["INC-001", "SVC-PAYMENT", "SVC-AUTH", "DEP-001"]
    assert path["edges"][-1] == {
        "type": "TARGETS",
        "source_id": "DEP-001",
        "target_id": "SVC-AUTH",
        "traversal_direction": "REVERSE",
    }
    assert auth["changes"][0]["graph_path"]["node_ids"][-1] == "CHG-001"
    # The established projection exposes a source_reference enum, never a raw source_ref.
    assert all(
        "source_ref" not in evidence
        and evidence["source_reference"] in {"WITHHELD", "NOT_AVAILABLE"}
        for evidence in investigation["evidence"]
    )
    assert "demo://" not in response.text
    assert (
        hashlib.sha256(database.read_bytes()).hexdigest() == before == public_demo.DATABASE_SHA256
    )


def test_case_native_comparisons_unknown_times_and_real_caps(public_client):
    data = public_client.get("/incidents/CASE-INC/dashboard").json()["investigation"]
    classes = [c["classification"] for c in data["contradictions"]]
    assert classes.count("CONFLICTING_OBSERVATIONS") == 1
    assert classes.count("UNDETERMINED") == 2
    assert any(e["evidence_observed_at"]["utc"] is None for e in data["evidence"])
    capped = public_client.get(
        "/incidents/CASE-INC/dashboard?max_candidates=1&max_evidence=1"
    ).json()["investigation"]
    assert len(capped["candidates"]) == len(capped["evidence"]) == 1
    assert capped["truncation"]["candidates"] and capped["truncation"]["evidence"]
    assert capped["causal_conclusion"] == "NOT_ESTABLISHED"
    unknown = public_client.get("/incidents/CASE-NO-TIME/dashboard").json()["investigation"]
    assert unknown["incident_time"]["utc"] is None


@pytest.mark.parametrize(
    "path",
    [
        "/console/models/capabilities",
        "/console/selection",
        "/console/agent/rehearse",
        "/console/agent/investigate",
        "/incidents",
        "/incidents/INC-001/context",
        "/incidents/INC-001/investigation",
        "/incidents/INC-001/explanation",
        "/ingest",
        "/cypher",
        "/query",
        "/admin",
        "/upload",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/examples/judge-demo/traceweaver-demo.rl",
        "/data/traceweaver.rl",
        "/assets/../LICENSE",
        "/assets/%2e%2e%2fLICENSE",
        "/incidents/%49NC-001/dashboard",
        "/console/incidents/",
    ],
)
def test_no_hidden_local_or_arbitrary_surface(public_client, path):
    for method in ("GET", "POST"):
        response = public_client.request(method, path)
        assert response.status_code == 404
        assert response.json() == {"detail": "Not found"}
        assert response.headers["content-security-policy"] == public_demo.CSP


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE"])
def test_read_routes_accept_get_only(public_client, method):
    for path in ("/", "/health", "/console/incidents", "/incidents/INC-001/dashboard"):
        response = public_client.request(method, path)
        assert response.status_code == 405
        assert response.headers["allow"] == "GET"
        assert response.headers["x-frame-options"] == "DENY"


@pytest.mark.parametrize(
    "query",
    [
        "mode=ollama",
        "model=qwen3:8b",
        "database=private.rl",
        "query=MATCH",
        "max_candidates=0",
        "max_candidates=101",
        "max_evidence=-1",
        "max_evidence=1000",
        "pre_minutes=1441",
        "post_minutes=-1",
        "pre_minutes=1.0",
        "pre_minutes=true",
        "pre_minutes=NaN",
        "max_candidates=1&max_candidates=2",
        "post_minutes=",
        "x=1",
    ],
)
def test_bounded_query_validation_without_input_echo(public_client, query):
    response = public_client.get("/incidents/INC-001/dashboard?" + query)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid public options"}


def test_unknown_incident_and_list_options_fail_safely(public_client):
    assert public_client.get("/incidents/ABSENT/dashboard").status_code == 404
    assert public_client.get("/console/incidents?limit=9999").status_code == 422
    assert public_client.get("/?incident=INC-001&selection=node:DEP-001").status_code == 200


def test_public_rehearsal_is_native_snapshot_bound_and_never_model_activity(
    public_client, public_setup, monkeypatch
):
    snapshot = public_client.get("/incidents/INC-001/dashboard").json()["source_fingerprint"]
    original, queries = GraphStore.execute, []

    def counted(store, statement, params=None):
        assert store.read_only is True
        queries.append(1)
        return original(store, statement, params)

    monkeypatch.setattr(GraphStore, "execute", counted)
    response = public_client.get("/public/rehearsal/INC-001?source_fingerprint=" + snapshot)
    assert response.status_code == 200
    report = response.json()
    assert report["mode_executed"] == "DETERMINISTIC_TOOL_REHEARSAL"
    assert not report["ai_directed_tools"] and not report["ai_generated_selection"]
    assert report["model_interactions"] == 0
    assert report["model_requested"] is report["model_executed"] is None
    assert len(queries) == report["native_query_count"] == 23
    assert [step["tool_name"] for step in report["tool_trace"]] == [
        "get_incident_scope",
        "trace_deployment",
        "inspect_evidence",
        "inspect_gaps",
    ]
    assert len(report["validated_claims"]) == 8 and report["validated_citation_count"] == 11
    assert report["source_fingerprint"] == snapshot
    database = public_setup.bundle / "traceweaver-demo.rl"
    assert hashlib.sha256(database.read_bytes()).hexdigest() == public_demo.DATABASE_SHA256
    assert public_client.post("/public/rehearsal/INC-001").status_code == 405


def test_public_rehearsal_rejects_stale_cross_incident_and_duplicate_snapshots(public_client):
    snapshot = public_client.get("/incidents/INC-001/dashboard").json()["source_fingerprint"]
    for identity, digest in [("INC-001", "0" * 64), ("CASE-INC", snapshot)]:
        response = public_client.get(f"/public/rehearsal/{identity}?source_fingerprint={digest}")
        assert response.status_code == 409
        assert response.json() == {"detail": "Public snapshot changed; refresh"}
    assert public_client.get("/public/rehearsal/INC-001").status_code == 422
    assert (
        public_client.get(
            f"/public/rehearsal/INC-001?source_fingerprint={snapshot}&source_fingerprint={snapshot}"
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "extra", ["model=qwen3:8b", "mode=ollama", "intent=RUN_MODEL", "confirmed=true", "query=MATCH"]
)
def test_public_rehearsal_cannot_admit_provider_or_query_arguments(public_client, extra):
    snapshot = public_client.get("/incidents/INC-001/dashboard").json()["source_fingerprint"]
    response = public_client.get(f"/public/rehearsal/INC-001?source_fingerprint={snapshot}&{extra}")
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid public options"}


def test_public_comparison_rehearsal_uses_only_declared_intent(public_client):
    snapshot = public_client.get("/incidents/CASE-INC/dashboard").json()["source_fingerprint"]
    query = urlencode({"source_fingerprint": snapshot, "intent": "RECONCILE_OBSERVATIONS"})
    report = public_client.get("/public/rehearsal/CASE-INC?" + query).json()
    assert report["intent"] == "RECONCILE_OBSERVATIONS"
    assert [step["tool_name"] for step in report["tool_trace"]].count("compare_observations") == 2
    assert report["model_interactions"] == 0


def test_public_rehearsal_uses_four_units_of_the_same_global_budget(public_setup):
    application = create_app(public_setup)
    with TestClient(application, base_url="https://demo.test") as client:
        snapshot = client.get("/incidents/INC-001/dashboard").json()["source_fingerprint"]
        application.state.public_resources.admission.tokens = 3
        assert (
            client.get("/public/rehearsal/INC-001?source_fingerprint=" + snapshot).status_code
            == 429
        )
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    "headers",
    [
        {"host": "evil.invalid"},
        {"host": "demo.test.evil.invalid"},
        {"origin": "https://evil.invalid"},
        {"origin": "null"},
        {"origin": "http://demo.test"},
        {"host": "evil.invalid", "x-forwarded-host": "demo.test"},
        {"host": "evil.invalid", "forwarded": "host=demo.test;proto=https"},
        {"origin": "http://demo.test", "x-forwarded-proto": "https"},
    ],
)
def test_public_host_origin_and_proxy_headers_fail_closed(public_client, headers):
    response = public_client.get("/health", headers=headers)
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


def test_same_origin_no_cors_duplicate_hosts_and_security_headers(public_client):
    response = public_client.get("/health", headers={"Origin": "https://demo.test"})
    assert response.status_code == 200
    assert response.headers["strict-transport-security"] == "max-age=31536000"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"] == public_demo.CSP
    assert "access-control-allow-origin" not in response.headers
    assert (
        public_client.get(
            "/health", headers=[("Host", "demo.test"), ("Host", "other.invalid")]
        ).status_code
        == 403
    )


def test_public_assets_are_explicit_not_a_filesystem_mount(public_client):
    assert public_client.get("/").status_code == 200
    for name in ("index-test.js", "index-test.css", "third-party-licenses.txt"):
        assert public_client.get("/assets/" + name).status_code == 200
    assert public_client.get("/assets/source.map").status_code == 404
    assert public_client.get("/assets/").status_code == 404


def test_request_body_and_query_header_limits(public_client):
    assert public_client.request("GET", "/health", content=b"untrusted").status_code == 400
    assert public_client.get("/?x=" + "a" * 2100).status_code == 400
    assert public_client.get("/health", headers={"X-Large": "a" * 17000}).status_code == 400


@pytest.mark.parametrize("broken", ["missing", "corrupt", "manifest", "local-build"])
def test_startup_rejects_unavailable_changed_or_wrong_mode(public_setup, broken):
    if broken == "missing":
        (public_setup.bundle / "traceweaver-demo.rl").unlink()
    elif broken == "corrupt":
        (public_setup.bundle / "traceweaver-demo.rl").write_bytes(b"corrupt owned copy")
    elif broken == "manifest":
        (public_setup.bundle / "MANIFEST.json").write_text("{}", encoding="utf8")
    else:
        (public_setup.assets / "index.html").write_text("local build", encoding="utf8")
    with pytest.raises(RuntimeError, match="^Public demo startup validation failed$"):
        with TestClient(create_app(public_setup), base_url="https://demo.test"):
            pytest.fail("Invalid deployment must not start")


def test_runtime_digest_change_returns_503_without_repair(public_client, public_setup):
    path = public_setup.bundle / "traceweaver-demo.rl"
    path.write_bytes(b"changed owned copy")
    response = public_client.get("/incidents/INC-001/dashboard")
    assert response.status_code == 503
    assert response.json() == {"detail": "Public graph unavailable"}
    assert public_client.get("/health").status_code == 503
    assert path.read_bytes() == b"changed owned copy"


@pytest.mark.parametrize("host", ["", "*", "https://demo.test", "bad@demo.test", "demo.test:99999"])
def test_missing_or_unsafe_host_configuration_does_not_start(public_setup, host):
    settings = PublicSettings(public_setup.bundle, (host,), public_setup.assets)
    with pytest.raises(RuntimeError, match="Public demo startup validation failed"):
        with TestClient(create_app(settings)):
            pytest.fail("Unsafe host configuration must not start")


def test_http_test_mode_cannot_enable_a_public_plaintext_origin(public_setup):
    settings = PublicSettings(public_setup.bundle, ("demo.test",), public_setup.assets, True)
    with pytest.raises(RuntimeError, match="Public demo startup validation failed"):
        with TestClient(create_app(settings)):
            pytest.fail("Plaintext is restricted to loopback test hosts")


def test_websocket_rejected(public_client):
    with pytest.raises(WebSocketDisconnect) as error:
        with public_client.websocket_connect("/console/agent/investigate"):
            pytest.fail("No public WebSocket surface")
    assert error.value.code == 1008


def test_no_network_or_legacy_database_override(public_setup, monkeypatch):
    monkeypatch.setenv("TRACEWEAVER_DATABASE", "private-user-store.rl")

    def deny(*args, **kwargs):
        pytest.fail("Public native reads must not create network connections")

    monkeypatch.setattr(socket, "create_connection", deny)
    with TestClient(create_app(public_setup), base_url="https://demo.test") as client:
        assert client.get("/incidents/CASE-INC/dashboard").status_code == 200
        assert client.get("/console/models/capabilities").status_code == 404


def test_two_native_workers_and_backpressure_recover(public_setup, monkeypatch):
    original = public_demo.dashboard
    both_entered, release = threading.Event(), threading.Event()
    lock, entered = threading.Lock(), []

    def gated(*args):
        with lock:
            entered.append(threading.get_ident())
            if len(entered) == 2:
                both_entered.set()
        assert release.wait(5), "Native worker gate must be released"
        return original(*args)

    monkeypatch.setattr(public_demo, "dashboard", gated)
    with TestClient(create_app(public_setup), base_url="https://demo.test") as client:
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(client.get, "/incidents/INC-001/dashboard") for _ in range(2)]
            try:
                assert both_entered.wait(5)
                response = client.get("/incidents/CASE-INC/dashboard")
                assert response.status_code == 429
                assert response.headers["retry-after"] == "2"
            finally:
                release.set()
            assert all(job.result().status_code == 200 for job in jobs)
        assert len(set(entered)) == 2
        assert client.get("/health").status_code == 200


def test_token_budget_does_not_depend_on_forged_client_ip(public_setup):
    application = create_app(public_setup)
    with TestClient(application, base_url="https://demo.test") as client:
        admission = application.state.public_resources.admission
        admission.tokens = 0
        response = client.get("/console/incidents", headers={"X-Forwarded-For": "203.0.113.1"})
        assert response.status_code == 429
        assert client.get("/health").status_code == 200
        admission.updated -= 2
        assert client.get("/console/incidents").status_code == 200


def test_unexpected_exception_is_generic_and_keeps_headers(public_client, monkeypatch):
    def fail(*args):
        raise RuntimeError("untrusted private details must never reach the client")

    monkeypatch.setattr(public_demo, "dashboard", fail)
    response = public_client.get("/incidents/INC-001/dashboard")
    assert response.status_code == 500
    assert response.json() == {"detail": "Public request failed"}
    assert response.headers["content-security-policy"] == public_demo.CSP


def test_public_launcher_keeps_one_worker_and_disables_proxy_trust(monkeypatch):
    calls = []
    monkeypatch.setenv("PORT", "10000")
    monkeypatch.setattr(public_server.uvicorn, "run", lambda *a, **kw: calls.append((a, kw)))
    public_server.main()
    ((args, options),) = calls
    assert args == ("traceweaver.public_demo:app",)
    assert options["workers"] == 1 and options["host"] == "0.0.0.0"
    assert options["proxy_headers"] is False and options["forwarded_allow_ips"] == ""
    assert options["access_log"] is False and options["ws"] == "none"


@pytest.mark.parametrize("port", ["0", "80", "65536", "-1", "10000;invalid", ""])
def test_invalid_public_port_cannot_launch(monkeypatch, port):
    monkeypatch.setenv("PORT", port)
    with pytest.raises(SystemExit, match="Invalid public service port"):
        public_server.main()
