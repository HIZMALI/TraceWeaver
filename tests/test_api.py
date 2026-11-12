from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.storage import GraphStore


def test_api_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database_engine": "relate",
        "persistent_store": True,
        "node_count": 21,
        "relationship_count": 27,
    }


def test_api_incidents(client):
    response = client.get("/incidents")
    assert response.status_code == 200
    assert {row["id"] for row in response.json()} == {"INC-001", "INC-002"}
    assert all({"title", "severity", "status"} <= row.keys() for row in response.json())


def test_api_incident_context(client):
    response = client.get("/incidents/INC-001/context")
    assert response.status_code == 200
    context = response.json()
    assert context["incident"]["id"] == "INC-001"
    assert context["context_paths"][0]["change_id"] == "CHG-001"
    assert len(context["evidence"]) == 4
    assert {r["deployment"]["id"] for r in context["related_deployments"]} == {"DEP-001", "DEP-002"}


def test_api_reads_store_changes_instead_of_fixture(client, database):
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "MATCH (e:Evidence {id: $id}) SET e.summary = $summary",
            {"id": "EVD-001", "summary": "Observed directly in the store"},
        )
    context = client.get("/incidents/INC-001/context").json()
    assert any(
        row["evidence"]["summary"] == "Observed directly in the store"
        for row in context["evidence"]
    )


def test_api_requests_never_modify_store(client, database):
    before = database.read_bytes()
    for endpoint in (
        "/health",
        "/incidents",
        "/incidents/INC-001/context",
        "/incidents/INC-002/context",
    ):
        assert client.get(endpoint).status_code == 200
    assert database.read_bytes() == before
    with GraphStore(database) as store:
        assert store.counts() == {"node_count": 21, "relationship_count": 27}


def test_api_concurrent_reads_keep_connection_thread_affinity(client):
    with ThreadPoolExecutor(max_workers=4) as executor:
        statuses = list(
            executor.map(lambda _: client.get("/incidents/INC-001/context").status_code, range(12))
        )
    assert statuses == [200] * 12


def test_unknown_incident(client):
    assert client.get("/incidents/does-not-exist/context").status_code == 404


def test_api_parameter_safety(client):
    payload = quote("INC-001' OR true", safe="")
    assert client.get(f"/incidents/{payload}/context").status_code == 404


@pytest.mark.parametrize("endpoint", ["/health", "/incidents", "/incidents/INC-001/context"])
def test_missing_database_returns_503_without_internal_details(tmp_path, endpoint):
    path = tmp_path / "private-system-path.rl"
    with TestClient(create_app(Settings(database=path))) as client:
        response = client.get(endpoint)
    assert response.status_code == 503
    assert response.json() == {"detail": "Graph database unavailable"}
    assert str(tmp_path) not in response.text
    assert not path.exists()


def test_corrupt_database_returns_503(tmp_path):
    path = tmp_path / "corrupt.rl"
    path.write_bytes(b"this is not a Relate file")
    with TestClient(create_app(Settings(database=path))) as client:
        assert client.get("/health").status_code == 503


def test_openapi_and_no_write_routes(client):
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {
        "/health",
        "/incidents",
        "/incidents/{incident_id}/context",
        "/incidents/{incident_id}/investigation",
    }
    assert all(set(path) == {"get"} for path in schema["paths"].values())
