import hashlib
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.storage import GraphStore


def test_new_dashboard_real_cross_process_writer_lock_is_generic(database):
    script = """
import json,sys
from fastapi.testclient import TestClient
from traceweaver.api import create_app
from traceweaver.config import Settings
with TestClient(create_app(Settings(database=sys.argv[1])),base_url='http://127.0.0.1') as c:
 r=c.get('/incidents/INC-001/dashboard')
 print(json.dumps({'status':r.status_code,'body':r.json()}))
"""
    with GraphStore(database, read_only=False):
        result = subprocess.run(
            [sys.executable, "-c", script, str(database)],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
    assert json.loads(result.stdout) == {
        "status": 503,
        "body": {"detail": "Graph database unavailable"},
    }


@pytest.mark.parametrize(
    "host",
    [
        "localhost:8000",
        "127.1:8000",
        "127.0.0.1:8001",
        "evil.example",
        "127.0.0.1.evil.example:8000",
        "[::1]:8000",
        "127.0.0.1:8000@evil.example",
    ],
)
def test_console_rejects_alternate_hosts_before_native_read(database, host):
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with TestClient(
        create_app(Settings(database=database)), base_url="http://127.0.0.1:8000"
    ) as client:
        response = client.get("/incidents/INC-001/dashboard", headers={"host": host})
    assert response.status_code == 403
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


@pytest.mark.parametrize(
    "origin",
    [
        "http://evil.example",
        "null",
        "http://localhost:8000",
        "http://127.0.0.1:8001",
        "https://127.0.0.1:8000",
    ],
)
def test_console_rejects_cross_origin_read(database, origin):
    with TestClient(
        create_app(Settings(database=database)), base_url="http://127.0.0.1:8000"
    ) as client:
        assert client.get("/console/incidents", headers={"origin": origin}).status_code == 403


def test_console_correct_numeric_origin_and_safe_headers(database):
    with TestClient(
        create_app(Settings(database=database)), base_url="http://127.0.0.1:8000"
    ) as client:
        response = client.get(
            "/incidents/INC-001/dashboard", headers={"origin": "http://127.0.0.1:8000"}
        )
    assert response.status_code == 200
    assert response.json()["investigation"]["incident_id"] == "INC-001"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "access-control-allow-origin" not in response.headers


def test_new_validation_error_never_reflects_private_input(database):
    with TestClient(create_app(Settings(database=database)), base_url="http://127.0.0.1") as client:
        response = client.get(
            "/incidents/INC-001/dashboard", params={"pre_minutes": "sk-private-value"}
        )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid console request"}


def test_duplicate_host_headers_are_rejected(database):
    with TestClient(create_app(Settings(database=database)), base_url="http://127.0.0.1") as client:
        response = client.get(
            "/console/incidents", headers=[("host", "127.0.0.1"), ("host", "evil.example")]
        )
    assert response.status_code == 403


def test_legacy_contracts_still_work_with_original_testclient_host(client):
    assert client.get("/health").status_code == 200
    assert client.get("/incidents/INC-001/explanation").json()["mode_executed"] == "DETERMINISTIC"


def test_static_api_fallback_does_not_shadow_unknown_routes(database):
    with TestClient(create_app(Settings(database=database)), base_url="http://127.0.0.1") as client:
        assert client.get("/console/not-a-route").status_code == 404
        assert client.get("/incidents/INC-001/not-a-route").status_code == 404
        assert client.get("/assets/../pyproject.toml").status_code == 404
