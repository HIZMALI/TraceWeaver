import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.explanation import explain
from traceweaver.storage import GraphStore

ENDPOINT = "/incidents/INC-001/explanation"


def cli(database, *args):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "explain",
            "--incident",
            "INC-001",
            "--database",
            str(database),
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_http_and_cli_exact_nondefault_response(client, database):
    before = database.read_bytes()
    response = client.get(
        ENDPOINT,
        params={"pre_minutes": 60, "post_minutes": 5, "max_candidates": 2, "max_evidence": 4},
    )
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
    assert response.status_code == 200 and result.returncode == 0
    assert response.json() == json.loads(result.stdout)
    assert database.read_bytes() == before


@pytest.mark.parametrize(
    "query",
    [
        "pre_minutes=-1",
        "post_minutes=1441",
        "pre_minutes=1.0",
        "max_candidates=0",
        "max_evidence=101",
        "pre_minutes=true",
    ],
)
def test_strict_explanation_query_limits(client, query):
    assert client.get(ENDPOINT + "?" + query).status_code == 422


def test_unknown_and_injection_ids_keep_404(client):
    for identity in ["unknown", "INC-001' OR true"]:
        response = client.get(f"/incidents/{identity}/explanation")
        assert response.status_code == 404
        assert response.json() == {"detail": "Incident not found"}


@pytest.mark.parametrize("contents", [None, b"not a relate graph"])
def test_missing_or_corrupt_graph_is_safe_503(tmp_path, contents):
    path = tmp_path / "synthetic-private-store.rl"
    if contents:
        path.write_bytes(contents)
    with TestClient(create_app(Settings(database=path))) as client:
        response = client.get(ENDPOINT)
    assert response.status_code == 503 and response.json() == {
        "detail": "Graph database unavailable"
    }
    assert str(tmp_path) not in response.text
    if not contents:
        assert not path.exists()


def test_actual_writer_lock_surfaces_503_in_separate_process(database):
    script = """
import sys,json
from traceweaver.api import create_app
from traceweaver.config import Settings
from fastapi.testclient import TestClient
with TestClient(create_app(Settings(database=sys.argv[1]))) as client:
    r=client.get('/incidents/INC-001/explanation')
    print(json.dumps({'status':r.status_code,'body':r.json()}))
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


def test_unexpected_explanation_error_is_generic_500(database, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic-private-provider-body")

    monkeypatch.setattr("traceweaver.api.explain", fail)
    with TestClient(
        create_app(Settings(database=database)), raise_server_exceptions=False
    ) as client:
        response = client.get(ENDPOINT)
    assert response.status_code == 500 and response.json() == {"detail": "Internal server error"}
    assert "synthetic-private" not in response.text


def test_http_cannot_enable_ollama_and_concurrent_reads_are_immutable(
    client, database, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("HTTP may never invoke a model")

    monkeypatch.setattr("traceweaver.explanation.OllamaLocal.select", forbidden)
    before = database.read_bytes()
    with ThreadPoolExecutor(max_workers=4) as workers:
        responses = list(
            workers.map(lambda _: client.get(ENDPOINT + "?mode=ollama&model=test"), range(8))
        )
    assert all(r.status_code == 200 for r in responses)
    assert all(r.json() == responses[0].json() for r in responses)
    assert responses[0].json()["mode_executed"] == "DETERMINISTIC"
    assert database.read_bytes() == before


def test_openapi_has_strict_report_and_only_get_routes(client):
    schema = client.get("/openapi.json").json()
    assert schema["paths"]["/incidents/{incident_id}/explanation"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"] == {"$ref": "#/components/schemas/ExplanationReport"}
    assert schema["components"]["schemas"]["ExplanationReport"]["additionalProperties"] is False
    assert all(set(route) == {"get"} for route in schema["paths"].values())


@pytest.mark.parametrize(
    "arguments",
    [
        ("--pre-minutes", "1.0"),
        ("--post-minutes", "1441"),
        ("--max-evidence", "0"),
        ("--mode", "cloud"),
    ],
)
def test_cli_argument_errors_stay_exit_two(database, arguments):
    result = cli(database, *arguments)
    assert result.returncode == 2 and "Traceback" not in result.stderr


def test_cli_unknown_missing_and_missing_model_are_explicit(database, tmp_path):
    missing = cli(tmp_path / "missing.rl")
    assert missing.returncode == 1 and "Traceback" not in missing.stderr
    assert str(tmp_path) not in missing.stderr
    unknown = subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "explain",
            "--database",
            str(database),
            "--incident",
            "unknown",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert unknown.returncode == 3
    unavailable = cli(database, "--mode", "ollama")
    assert unavailable.returncode == 12
    body = json.loads(unavailable.stdout)
    assert body["explanation_status"] == "MODEL_UNAVAILABLE" and body["mode_executed"] == "NONE"


def test_sensitive_graph_identifier_is_not_disclosed_by_http(database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (s:Service {id:'SVC-PAYMENT'}) SET s.id=$id",
            {"id": "C:/synthetic-private/secret"},
        )
    with TestClient(create_app(Settings(database=database))) as client:
        response = client.get(ENDPOINT)
    assert response.status_code == 503
    assert "synthetic-private" not in response.text


def test_all_http_fields_equal_real_service(client, database):
    assert client.get(ENDPOINT).json() == explain(database, "INC-001").model_dump(mode="json")
