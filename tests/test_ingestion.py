import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from traceweaver.ingestion import ingest
from traceweaver.ingestion_models import MAX_NODES, MAX_RELATIONSHIPS
from traceweaver.investigation import investigate
from traceweaver.local_files import MAX_INPUT_BYTES
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "fixtures/ingestion_example.json"


def payload():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def write_payload(tmp_path, data, name="input.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_default_dry_run_does_not_create_store_or_directory(tmp_path):
    database = tmp_path / "not-created" / "scratch.rl"
    result = ingest(EXAMPLE, database)
    assert result["mode"] == "DRY_RUN" and not result["committed"]
    assert result["status"] == "VALIDATED_NOT_COMMITTED"
    assert result["graph_counts"] is None
    assert result["counts"]["nodes_created"] == 0
    assert result["counts"]["nodes_would_create"] == 8
    assert result["counts"]["relationships_would_create"] == 9
    assert not database.parent.exists()


def test_three_applies_are_idempotent_and_topology_is_real(tmp_path):
    database = tmp_path / "scratch.rl"
    for run in range(3):
        result = ingest(EXAMPLE, database, apply=True)
        assert result["committed"] and result["mode"] == "APPLY"
        assert result["graph_counts"] == {"node_count": 8, "relationship_count": 9}
        assert result["counts"]["nodes_created"] == (8 if run == 0 else 0)
        assert result["counts"]["relationships_created"] == (9 if run == 0 else 0)
        assert result["counts"]["nodes_already_present"] == (0 if run == 0 else 8)
    before = digest(database)
    dry = ingest(EXAMPLE, database)
    assert dry["counts"]["nodes_would_create"] == 0
    assert digest(database) == before
    with GraphStore(database) as store:
        review = investigate(store, "ING-INC-001")
        assert review.candidates[0].changes[0].graph_path.node_ids == [
            "ING-INC-001",
            "ING-API",
            "ING-AUTH",
            "ING-DEP-001",
            "ING-CHG-001",
        ]
        assert review.contradiction_audit.conflict_count == 1
        assert review.causal_conclusion == "NOT_ESTABLISHED"


@pytest.mark.parametrize(
    "problem",
    [
        "version",
        "label",
        "edge_type",
        "direction",
        "dangling",
        "duplicate_node",
        "duplicate_edge",
        "dataset",
        "property_name",
        "property_type",
        "property_id",
        "source_field",
        "origin",
        "nested_property",
    ],
)
def test_invalid_batches_reject_before_writer_creation(tmp_path, problem):
    data = payload()
    if problem == "version":
        data["contract_version"] = "99"
    elif problem == "label":
        data["nodes"][0]["label"] = "Untrusted) MATCH (n)"
    elif problem == "edge_type":
        data["relationships"][0]["type"] = "CAUSED_BY"
    elif problem == "direction":
        edge = data["relationships"][0]
        edge["source"], edge["target"] = edge["target"], edge["source"]
    elif problem == "dangling":
        data["relationships"][0]["target"]["id"] = "absent"
    elif problem == "duplicate_node":
        data["nodes"].append(deepcopy(data["nodes"][0]))
    elif problem == "duplicate_edge":
        data["relationships"].append(deepcopy(data["relationships"][0]))
    elif problem == "dataset":
        data["nodes"][0]["properties"]["dataset_id"] = "different-owner"
    elif problem == "property_name":
        data["nodes"][0]["properties"]["unapproved"] = "literal"
    elif problem == "property_type":
        data["nodes"][0]["properties"]["demo"] = 1
    elif problem == "property_id":
        data["nodes"][0]["properties"]["id"] = "different-id"
    elif problem == "source_field":
        del data["source"]["captured_at"]
    elif problem == "origin":
        data["nodes"][0]["properties"]["demo"] = False
    else:
        data["nodes"][0]["properties"]["summary"] = {"nested": "not-admitted"}
    database = tmp_path / "not-created" / "batch.rl"
    with pytest.raises(ToolError) as error:
        ingest(write_payload(tmp_path, data), database, apply=True)
    assert error.value.code == "INVALID_INGESTION_DOCUMENT"
    assert not database.parent.exists()


def test_node_edge_count_boundaries_and_overflow(tmp_path):
    data = payload()
    service = deepcopy(data["nodes"][1])
    data["nodes"] = []
    for index in range(MAX_NODES):
        node = deepcopy(service)
        node["id"] = node["properties"]["id"] = f"ADMISSION-{index}"
        data["nodes"].append(node)
    data["relationships"] = [
        {
            "type": "DEPENDS_ON",
            "source": {"label": "Service", "id": f"ADMISSION-{i}"},
            "target": {"label": "Service", "id": f"ADMISSION-{(i + delta) % MAX_NODES}"},
        }
        for i in range(MAX_NODES)
        for delta in (1, 2)
    ]
    database = tmp_path / "not-created" / "limit.rl"
    result = ingest(write_payload(tmp_path, data), database)
    assert result["input_counts"] == {"nodes": MAX_NODES, "relationships": MAX_RELATIONSHIPS}
    for key in ("nodes", "relationships"):
        invalid = deepcopy(data)
        invalid[key].append(deepcopy(invalid[key][0]))
        with pytest.raises(ToolError, match="validation"):
            ingest(write_payload(tmp_path, invalid), database, apply=True)
    assert not database.parent.exists()


def test_file_string_and_nesting_limits_before_writer(tmp_path):
    database = tmp_path / "not-created" / "large.rl"
    huge = tmp_path / "too-large.json"
    with huge.open("wb") as output:
        output.truncate(MAX_INPUT_BYTES + 1)
    with pytest.raises(ToolError) as error:
        ingest(huge, database, apply=True)
    assert error.value.code == "INPUT_TOO_LARGE"
    data = payload()
    data["nodes"][0]["properties"]["summary"] = "\U0001f331" * 1024
    assert ingest(write_payload(tmp_path, data), database)["mode"] == "DRY_RUN"
    data["nodes"][0]["properties"]["summary"] += "\U0001f331"
    with pytest.raises(ToolError, match="validation"):
        ingest(write_payload(tmp_path, data), database, apply=True)
    deep = tmp_path / "deep.json"
    deep.write_text('{"nested":' + "[" * 9 + "0" + "]" * 9 + "}")
    with pytest.raises(ToolError) as error:
        ingest(deep, database, apply=True)
    assert error.value.code == "JSON_DEPTH_LIMIT"
    assert not database.parent.exists()


@pytest.mark.parametrize(
    "text", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"secret": BROKEN}']
)
def test_nonstandard_json_is_rejected_without_body_dump(tmp_path, text):
    source = tmp_path / "bad.json"
    source.write_text(text)
    with pytest.raises(ToolError) as error:
        ingest(source, tmp_path / "absent.rl", apply=True)
    assert "BROKEN" not in json.dumps(error.value.as_dict())
    assert not (tmp_path / "absent.rl").exists()


@pytest.mark.parametrize("marker", [False, None])
def test_non_demo_or_unknown_requires_additional_flag(tmp_path, marker):
    data = payload()
    data["source"]["declared_origin"] = "NON_SYNTHETIC" if marker is False else "UNKNOWN"
    for node in data["nodes"]:
        node["properties"]["demo"] = marker
    source = write_payload(tmp_path, data)
    database = tmp_path / "non-demo-guard.rl"
    with pytest.raises(ToolError) as error:
        ingest(source, database, apply=True)
    assert error.value.code == "NON_DEMO_REQUIRES_OPT_IN" and not database.exists()
    assert ingest(source, database, apply=True, allow_non_demo=True)["committed"]
    with GraphStore(database) as store:
        review = investigate(store, "ING-INC-001")
    assert review.is_demo is marker
    assert review.causal_conclusion == "NOT_ESTABLISHED"


def test_known_conflicting_user_node_is_rejected_before_writer_and_preserves_bytes(tmp_path):
    database = tmp_path / "conflict.rl"
    with GraphStore(database, read_only=False) as store:
        store.execute(
            "CREATE (:Service {id: $id, name: $name, user_note: $note})",
            {"id": "ING-AUTH", "name": "User-owned service", "note": "preserve exactly"},
        )
    before = digest(database)
    with pytest.raises(ToolError) as error:
        ingest(EXAMPLE, database, apply=True)
    assert error.value.code == "INGEST_CONFLICT"
    assert error.value.as_dict()["created_nodes"] == 0
    assert digest(database) == before
    with GraphStore(database) as store:
        assert store.counts() == {"node_count": 1, "relationship_count": 0}
        assert store.execute("MATCH (n:Service) RETURN n.user_note AS note LIMIT 1") == [
            {"note": "preserve exactly"}
        ]


def test_conflict_after_preflight_rolls_back_real_earlier_inserts(tmp_path, monkeypatch):
    import traceweaver.ingestion as ingestion_module

    database = tmp_path / "race-rollback.rl"
    properties = payload()["nodes"][2]["properties"]
    with GraphStore(database, read_only=False) as store:
        store.execute("CREATE (s:Service) SET s += $properties", {"properties": properties})
    observed = {"race_injected": False, "early_insert_seen": False}

    class RealRaceStore(GraphStore):
        def __enter__(self):
            if not self.read_only and not observed["race_injected"]:
                observed["race_injected"] = True
                with GraphStore(database, read_only=False) as racer:
                    racer.execute(
                        "MATCH (s:Service {id:$id}) SET s.name=$name",
                        {"id": "ING-AUTH", "name": "Preserve committed racing change"},
                    )
            return super().__enter__()

        def execute(self, statement, params=None):
            rows = super().execute(statement, params)
            if statement.startswith("MERGE (n:Incident"):
                inserted = super().execute(
                    "MATCH (n:Incident {id:$id}) RETURN count(n) AS n", {"id": "ING-INC-001"}
                )
                assert inserted == [{"n": 1}]
                observed["early_insert_seen"] = True
            return rows

    monkeypatch.setattr(ingestion_module, "GraphStore", RealRaceStore)
    with pytest.raises(ToolError) as error:
        ingest(EXAMPLE, database, apply=True)
    assert error.value.code == "INGEST_CONFLICT"
    assert observed == {"race_injected": True, "early_insert_seen": True}
    with GraphStore(database) as store:
        assert store.counts() == {"node_count": 1, "relationship_count": 0}
        assert store.execute("MATCH (n:Service) RETURN n.name AS name LIMIT 1") == [
            {"name": "Preserve committed racing change"}
        ]
        assert store.execute("SHOW CONSTRAINTS") == []


def test_existing_fixtures_user_nodes_and_extra_properties_survive(database):
    result = ingest(EXAMPLE, database, apply=True)
    assert result["graph_counts"] == {"node_count": 29, "relationship_count": 36}
    with GraphStore(database, read_only=False) as store:
        store.execute("CREATE (:UserNote {id:'ingestion-user', text:'keep me'})")
        store.execute(
            "MATCH (n:Service {id:$id}) SET n.user_note=$note",
            {"id": "ING-AUTH", "note": "extra property"},
        )
    before = digest(database)
    assert not ingest(EXAMPLE, database)["committed"]
    assert digest(database) == before
    assert ingest(EXAMPLE, database, apply=True)["graph_counts"] == {
        "node_count": 30,
        "relationship_count": 36,
    }
    with GraphStore(database) as store:
        assert store.execute(
            "MATCH (n:Service {id:$id}) RETURN n.user_note AS note LIMIT 1", {"id": "ING-AUTH"}
        ) == [{"note": "extra property"}]
        assert store.execute(
            "MATCH (i:Incident {id:$id}) RETURN i.id AS id LIMIT 1", {"id": "INC-001"}
        )
        assert store.execute("MATCH (u:UserNote) RETURN u.text AS text LIMIT 1") == [
            {"text": "keep me"}
        ]


def test_relationship_ownership_conflicts_preserve_existing_graph(tmp_path):
    database = tmp_path / "edge-conflict.rl"
    ingest(EXAMPLE, database, apply=True)
    with GraphStore(database, read_only=False) as store:
        store.execute("MATCH ()-[r:TARGETS]->() SET r.dataset_id = $owner", {"owner": "user-owned"})
    before = digest(database)
    with pytest.raises(ToolError) as error:
        ingest(EXAMPLE, database, apply=True)
    assert error.value.code == "INGEST_CONFLICT"
    assert digest(database) == before


def test_invalid_event_time_is_preserved_with_unknown_not_ingestion_fallback(tmp_path):
    data = payload()
    data["nodes"][5]["properties"]["timestamp"] = "2026-11-12T10:05:00"
    data["nodes"][5]["properties"]["ingested_at"] = "2026-11-12T10:10:00Z"
    database = tmp_path / "unknown.rl"
    result = ingest(write_payload(tmp_path, data), database, apply=True)
    assert any(w["code"] == "INVALID_TIMESTAMP" for w in result["warnings"])
    with GraphStore(database) as store:
        review = investigate(store, "ING-INC-001")
    item = next(e for e in review.evidence if e.evidence_id == "ING-E-HEALTHY")
    assert item.evidence_observed_at.original == "2026-11-12T10:05:00"
    assert item.evidence_observed_at.utc is None and item.temporal_classification == "UNKNOWN"


def test_literal_values_are_parameterized_and_not_executed(tmp_path):
    data = payload()
    literal = "x' MATCH (n) RETURN n //"
    data["nodes"][1]["properties"]["name"] = literal
    data["nodes"][1]["id"] = data["nodes"][1]["properties"]["id"] = literal
    for edge in data["relationships"]:
        for endpoint in (edge["source"], edge["target"]):
            if endpoint["id"] == "ING-API":
                endpoint["id"] = literal
    database = tmp_path / "parameters.rl"
    ingest(write_payload(tmp_path, data), database, apply=True)
    with GraphStore(database) as store:
        assert store.execute(
            "MATCH (s:Service {id:$id}) RETURN s.name AS name LIMIT 1", {"id": literal}
        ) == [{"name": literal}]
        assert store.counts() == {"node_count": 8, "relationship_count": 9}


def test_locked_store_error_is_safe_and_does_not_retry(tmp_path):
    database = tmp_path / "locked.rl"
    ingest(EXAMPLE, database, apply=True)
    with GraphStore(database, read_only=False):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "traceweaver",
                "ingest",
                "--input",
                str(EXAMPLE),
                "--database",
                str(database),
                "--apply",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert result.returncode == 10
    assert json.loads(result.stderr)["error"]["code"] == "GRAPH_STORE_LOCKED"
    assert str(tmp_path) not in result.stderr and "Traceback" not in result.stderr


def test_invalid_cli_payload_does_not_echo_secret_values(tmp_path):
    data = payload()
    data["nodes"][0]["properties"]["summary"] = {"secret": "DO_NOT_DISCLOSE_IMPORT_BODY"}
    source = write_payload(tmp_path, data)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "ingest",
            "--input",
            str(source),
            "--database",
            str(tmp_path / "absent.rl"),
            "--apply",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 4
    assert json.loads(result.stderr)["error"]["code"] == "INVALID_INGESTION_DOCUMENT"
    assert "DO_NOT_DISCLOSE" not in result.stderr and str(tmp_path) not in result.stderr


def test_ingest_cli_defaults_to_dry_run_and_applies_three_times(tmp_path):
    database = tmp_path / "cli-ingestion.rl"
    expected = hashlib.sha256(EXAMPLE.read_bytes()).hexdigest()
    arguments = [
        sys.executable,
        "-m",
        "traceweaver",
        "ingest",
        "--input",
        str(EXAMPLE),
        "--database",
        str(database),
        "--expected-sha256",
        expected,
    ]
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=30, check=True)
    assert json.loads(result.stdout)["mode"] == "DRY_RUN" and not database.exists()
    for run in range(3):
        result = subprocess.run(
            [*arguments, "--apply"], capture_output=True, text=True, timeout=30, check=True
        )
        body = json.loads(result.stdout)
        assert body["integrity"]["comparison_status"] == "MATCH"
        assert body["external_verification_status"] == "NOT_PERFORMED"
        assert body["counts"]["nodes_created"] == (8 if run == 0 else 0)
        assert body["graph_counts"] == {"node_count": 8, "relationship_count": 9}
