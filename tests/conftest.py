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
