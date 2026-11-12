import json
from importlib.resources import files
from pathlib import Path

import pytest
from pydantic import ValidationError

from traceweaver.seed import load_fixture, seed_database
from traceweaver.storage import GraphStore, QueryError


def test_fixture_loading(database):
    with GraphStore(database) as store:
        assert store.counts() == {"node_count": 21, "relationship_count": 27}
        assert store.execute("MATCH (i:Incident) RETURN count(i) AS n") == [{"n": 2}]
        assert store.execute("MATCH (n) WHERE n.demo = true RETURN count(n) AS n") == [{"n": 21}]
        assert store.execute("MATCH ()-[r]->() WHERE r.demo = true RETURN count(r) AS n") == [
            {"n": 27}
        ]


def test_idempotent_seed_three_runs(database):
    for _ in range(2):
        assert seed_database(database) == {"node_count": 21, "relationship_count": 27}


def test_existing_data_preserved_and_no_accidental_reset(tmp_path):
    path = tmp_path / "user-data.rl"
    with GraphStore(path, read_only=False) as store:
        store.execute(
            "CREATE (:UserNote {id: $id, text: $text})-[:REFERENCES]->(:UserNote {id: $other})",
            {"id": "user-owned", "text": "keep this exactly", "other": "user-other"},
        )
    for _ in range(3):
        assert seed_database(path) == {"node_count": 23, "relationship_count": 28}
    with GraphStore(path) as store:
        assert store.execute(
            "MATCH (n:UserNote {id: $id})-[:REFERENCES]->(m:UserNote) "
            "RETURN n.text AS text, m.id AS target LIMIT 1",
            {"id": "user-owned"},
        ) == [{"text": "keep this exactly", "target": "user-other"}]


def test_seed_conflict_rolls_back_earlier_inserts(tmp_path):
    path = tmp_path / "conflict.rl"
    # This ID occurs after the two incidents, so the failure must undo earlier inserts.
    with GraphStore(path, read_only=False) as store:
        store.execute(
            "CREATE (:Service {id: $id, name: $name})", {"id": "SVC-AUTH", "name": "Mine"}
        )
    with pytest.raises(QueryError, match="Seed conflict"):
        seed_database(path)
    with GraphStore(path) as store:
        assert store.counts() == {"node_count": 1, "relationship_count": 0}
        assert store.execute("MATCH (s:Service) RETURN s.name AS name LIMIT 1") == [
            {"name": "Mine"}
        ]


def test_constraint_failure_rolls_back_nodes_and_relationships(tmp_path):
    path = tmp_path / "rollback.rl"
    with GraphStore(path, read_only=False) as store:
        with pytest.raises(QueryError):
            with store.transaction():
                store.execute("CREATE CONSTRAINT rollback_id FOR (n:Probe) REQUIRE n.id IS UNIQUE")
                store.execute("CREATE (:Probe {id: 'one'})-[:LINKS]->(:Probe {id: 'two'})")
                store.execute("CREATE (:Probe {id: 'one'})")
        assert store.counts() == {"node_count": 0, "relationship_count": 0}
    with GraphStore(path) as store:
        assert store.counts() == {"node_count": 0, "relationship_count": 0}


def test_fixture_is_valid_and_packaged_copy_matches():
    canonical = Path(__file__).resolve().parents[1] / "fixtures/demo_incidents.json"
    packaged = files("traceweaver").joinpath("fixtures/demo_incidents.json")
    assert json.loads(canonical.read_text()) == json.loads(packaged.read_text())
    fixture = load_fixture(canonical)
    assert len(fixture.nodes) >= 20
    assert len(fixture.relationships) >= 25
    assert all(
        node.properties["source_ref"].startswith("demo://")
        for node in fixture.nodes
        if "source_ref" in node.properties
    )


def test_invalid_fixture_does_not_create_store(tmp_path):
    data = load_fixture().model_dump()
    data["relationships"][0]["type"] = "CAUSED_BY"
    fixture = tmp_path / "invalid.json"
    fixture.write_text(json.dumps(data))
    path = tmp_path / "not-created.rl"
    with pytest.raises(ValidationError, match="Unsupported relationship"):
        seed_database(path, fixture)
    assert not path.exists()


def test_unique_ids_are_enforced(database):
    with GraphStore(database, read_only=False) as store:
        with pytest.raises(QueryError):
            store.execute("CREATE (:Incident {id: $id})", {"id": "INC-001"})
        assert store.counts()["node_count"] == 21
