import relate

from traceweaver.storage import GraphStore


def test_embedded_engine_smoke():
    with relate.connect(":memory:") as connection:
        connection.execute(
            "CREATE (a:Smoke {id: $a})-[:LINKS]->(b:Smoke {id: $b})",
            {"a": "first", "b": "second"},
        )
        assert connection.execute(
            "MATCH (a:Smoke)-[:LINKS]->(b:Smoke) RETURN a.id AS source, b.id AS target LIMIT 10"
        ).fetchall() == [{"source": "first", "target": "second"}]


def test_database_creation(tmp_path):
    path = tmp_path / "new" / "store.rl"
    with GraphStore(path, read_only=False) as store:
        store.execute("CREATE (:Smoke {id: $id})", {"id": "created"})
        assert store.counts() == {"node_count": 1, "relationship_count": 0}
    assert path.is_file()
