import json
import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.storage import GraphStore

ENDPOINT = "/incidents/INC-001/investigation"


def cli(database, *arguments):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "investigate",
            "--incident",
            "INC-001",
            "--database",
            str(database),
            *arguments,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_http_and_cli_share_exact_investigation_contract(client, database):
    before = database.read_bytes()
    response = client.get(
        ENDPOINT,
        params={"pre_minutes": 60, "post_minutes": 5, "max_candidates": 2, "max_evidence": 4},
    )
    assert response.status_code == 200
    result = cli(
        database,
        "--pre-minutes",
        "60",
        "--post-minutes",
        "5",
        "--max-candidates",
        "2",
        "--max-evidence",
        "4",
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == response.json()
    assert response.json()["causal_conclusion"] == "NOT_ESTABLISHED"
    assert database.read_bytes() == before


@pytest.mark.parametrize(
    "query",
    [
        "pre_minutes=-1",
        "post_minutes=1441",
        "pre_minutes=1.0",
        "post_minutes=1.5",
        "max_candidates=0",
        "max_evidence=101",
        "max_candidates=true",
        "pre_minutes=0%20OR%201=1",
    ],
)
def test_api_strict_window_and_limit_validation(client, query):
    assert client.get(f"{ENDPOINT}?{query}").status_code == 422


def test_api_unknown_and_injection_ids_return_404(client):
    for id in ["unknown", "INC-001' OR true"]:
        response = client.get(f"/incidents/{quote(id, safe='')}/investigation")
        assert response.status_code == 404
        assert response.json() == {"detail": "Incident not found"}


def test_missing_and_corrupt_store_errors_are_safe_503(tmp_path):
    path = tmp_path / "private-location.rl"
    for contents in [None, b"not a graph"]:
        if contents:
            path.write_bytes(contents)
        with TestClient(create_app(Settings(database=path))) as client:
            response = client.get(ENDPOINT)
            assert response.status_code == 503
            assert response.json() == {"detail": "Graph database unavailable"}
            assert str(tmp_path) not in response.text


def test_locked_store_investigation_returns_503_in_another_process(database):
    script = """
import json, sys
from fastapi.testclient import TestClient
from traceweaver.api import create_app
from traceweaver.config import Settings
with TestClient(create_app(Settings(database=sys.argv[1]))) as client:
    r = client.get('/incidents/INC-001/investigation')
    print(json.dumps({'status': r.status_code, 'body': r.json()}))
"""
    with GraphStore(database, read_only=False):
        result = subprocess.run(
            [sys.executable, "-c", script, str(database)],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    assert json.loads(result.stdout) == {
        "status": 503,
        "body": {"detail": "Graph database unavailable"},
    }


def test_unexpected_failure_logs_server_details_but_returns_generic_500(database, caplog):
    application = create_app(Settings(database=database))

    @application.get("/test-unexpected-failure")
    def fail():
        raise RuntimeError("private-test-path: deliberately unexpected failure")

    with (
        caplog.at_level(logging.ERROR),
        TestClient(application, raise_server_exceptions=False) as client,
    ):
        response = client.get("/test-unexpected-failure")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "private-test-path" not in response.text
    assert "private-test-path" in caplog.text


def test_new_endpoint_concurrency_preserves_thread_affinity_and_store_bytes(client, database):
    before = database.read_bytes()
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda _: client.get(ENDPOINT), range(12)))
    assert all(response.status_code == 200 for response in responses)
    assert all(response.json() == responses[0].json() for response in responses)
    assert database.read_bytes() == before


def test_api_returns_partial_instead_of_failing_on_missing_anchor(case_database):
    with TestClient(create_app(Settings(database=case_database))) as client:
        response = client.get("/incidents/CASE-NO-TIME/investigation")
    assert response.status_code == 200
    assert response.json()["investigation_status"] == "PARTIAL_CONTEXT"
    assert response.json()["incident_started_at"] is None


@pytest.mark.parametrize(
    "arguments",
    [
        ("--pre-minutes", "1.0"),
        ("--post-minutes", "1441"),
        ("--max-candidates", "101"),
        ("--max-evidence", "0"),
    ],
)
def test_cli_argument_failures_preserve_exit_two(database, arguments):
    result = cli(database, *arguments)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_cli_expected_error_exit_codes(database, tmp_path):
    missing = cli(tmp_path / "not-created.rl")
    assert missing.returncode == 1 and "not found" in missing.stderr
    unknown = subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "investigate",
            "--incident",
            "unknown",
            "--database",
            str(database),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert unknown.returncode == 3
    assert unknown.stderr.strip() == "Incident not found"
