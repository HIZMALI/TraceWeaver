import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.seed import seed_database


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "integration.rl"
    seed_database(path)
    return path


@pytest.fixture
def client(database: Path):
    with TestClient(create_app(Settings(database=database))) as test_client:
        yield test_client


@pytest.fixture
def case_database(database: Path) -> Path:
    fixture = Path(__file__).resolve().parents[1] / "fixtures/sprint01_cases.json"
    seed_database(database, fixture)
    return database


@pytest.fixture(scope="session", autouse=True)
def preserve_workspace_stores():
    """Guard all pre-existing workspace stores without ever opening them for writing."""
    root = Path(__file__).resolve().parents[1]
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (root / "data").glob("*.rl")
    }
    yield
    for path, fingerprint in before.items():
        assert path.is_file(), f"A pre-existing workspace store disappeared: {path.name}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == fingerprint, path.name
