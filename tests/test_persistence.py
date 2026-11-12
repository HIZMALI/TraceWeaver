import json
import subprocess
import sys

import pytest

from traceweaver.queries import MULTI_HOP_CONTEXT
from traceweaver.storage import DatabaseUnavailable, GraphStore, QueryError


def test_persistence_across_reopening(database):
    for _ in range(2):
        with GraphStore(database) as store:
            assert store.counts() == {"node_count": 21, "relationship_count": 27}
            assert (
                store.execute(MULTI_HOP_CONTEXT, {"incident_id": "INC-001", "limit": 1})[0][
                    "change_id"
                ]
                == "CHG-001"
            )


def test_persistence_in_separate_python_process(database):
    script = """
import json, sys, relate
with relate.connect(sys.argv[1], read_only=True) as c:
    row = c.execute('MATCH (:Incident {id: $id})-[:AFFECTS]->(:Service)'
                    '-[:DEPENDS_ON]->(s:Service)<-[:TARGETS]-(d:Deployment)'
                    '-[:INCLUDES_CHANGE]->(ch:Change) '
                    'RETURN s.id AS service, d.id AS deployment, ch.id AS change LIMIT 10',
                    {'id': 'INC-001'}).fetchall()
    print(json.dumps(row))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(database)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout) == [
        {"service": "SVC-AUTH", "deployment": "DEP-001", "change": "CHG-001"}
    ]


def test_read_only_rejects_writes_and_store_bytes_unchanged(database):
    before = database.read_bytes()
    with GraphStore(database) as store:
        with pytest.raises(DatabaseUnavailable, match="read.only"):
            store.execute("CREATE (:Probe {id: 'must-not-exist'})")
        with pytest.raises(QueryError, match="writable"):
            with store.transaction():
                pass
        assert store.counts()["node_count"] == 21
    assert database.read_bytes() == before


def test_missing_store_read_does_not_create_it(tmp_path):
    path = tmp_path / "missing" / "db.rl"
    with pytest.raises(DatabaseUnavailable, match="not found"):
        with GraphStore(path):
            pass
    assert not path.parent.exists()


def test_writer_lock_is_not_hidden(database):
    script = """
import sys, relate
try:
    with relate.connect(sys.argv[1], read_only=True):
        pass
except relate.OperationalError as e:
    print(str(e))
    sys.exit(5)
sys.exit(0)
"""
    with GraphStore(database, read_only=False):
        result = subprocess.run(
            [sys.executable, "-c", script, str(database)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert result.returncode == 5
    assert "locked" in result.stdout.lower()
