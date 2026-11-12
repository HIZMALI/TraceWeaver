import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from traceweaver.judge_demo import ARTIFACT_NAME, build_judge_demo, verify_judge_demo
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError

ROOT = Path(__file__).resolve().parents[1]


def test_generated_bundle_has_real_synthetic_graph_and_matching_manifest(tmp_path):
    output = tmp_path / "fresh-bundle"
    manifest = build_judge_demo(output)
    artifact = output / ARTIFACT_NAME
    assert manifest["synthetic_only"] and manifest["relate_version"] == "1.0.0"
    assert manifest["graph_counts"] == {"node_count": 51, "relationship_count": 67}
    assert manifest["artifact_size_bytes"] == artifact.stat().st_size < 8 * 1024 * 1024
    assert manifest["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    with GraphStore(artifact) as store:
        assert store.execute("MATCH (n) WHERE n.demo = true RETURN count(n) AS n") == [{"n": 51}]
        assert store.execute("MATCH ()-[r]->() WHERE r.demo = true RETURN count(r) AS n") == [
            {"n": 67}
        ]
    assert verify_judge_demo(output) == manifest


def test_packaged_public_artifact_opens_read_only_without_byte_changes():
    output = ROOT / "examples/judge-demo"
    before = (output / ARTIFACT_NAME).read_bytes()
    manifest = verify_judge_demo(output)
    assert manifest["artifact_sha256"] == hashlib.sha256(before).hexdigest()
    assert (output / ARTIFACT_NAME).read_bytes() == before


def test_overwrite_requires_force_for_intact_generated_artifacts(tmp_path):
    output = tmp_path / "bundle"
    first = build_judge_demo(output)
    before = (output / ARTIFACT_NAME).read_bytes()
    with pytest.raises(ToolError) as error:
        build_judge_demo(output)
    assert error.value.code == "JUDGE_OUTPUT_EXISTS"
    assert (output / ARTIFACT_NAME).read_bytes() == before
    second = build_judge_demo(output, force=True)
    assert first["logical_graph_sha256"] == second["logical_graph_sha256"]
    assert first["graph_counts"] == second["graph_counts"]


def test_force_cannot_overwrite_a_user_store_or_unknown_manifest(tmp_path):
    output = tmp_path / "unowned"
    output.mkdir()
    artifact = output / ARTIFACT_NAME
    with GraphStore(artifact, read_only=False) as store:
        store.execute("CREATE (:UserNote {id:'user-owned', text:'keep this'})")
    before = artifact.read_bytes()
    with pytest.raises(ToolError) as error:
        build_judge_demo(output, force=True)
    assert error.value.code == "UNSAFE_JUDGE_REPLACEMENT"
    assert artifact.read_bytes() == before


def test_force_rejects_user_edits_to_a_previously_generated_manifest(tmp_path):
    output = tmp_path / "edited-manifest"
    build_judge_demo(output)
    path = output / "MANIFEST.json"
    data = json.loads(path.read_text())
    data["user_note"] = "preserve this independent change"
    path.write_text(json.dumps(data))
    before = (output / ARTIFACT_NAME).read_bytes(), path.read_bytes()
    with pytest.raises(ToolError, match="intact verified"):
        build_judge_demo(output, force=True)
    assert ((output / ARTIFACT_NAME).read_bytes(), path.read_bytes()) == before


def test_forged_hash_manifest_does_not_authorize_overwriting_modified_user_graph(tmp_path):
    output = tmp_path / "modified-graph"
    build_judge_demo(output)
    artifact = output / ARTIFACT_NAME
    with GraphStore(artifact, read_only=False) as store:
        store.execute("CREATE (:UserNote {id:'user-data', demo:false})")
    path = output / "MANIFEST.json"
    manifest = json.loads(path.read_text())
    manifest["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest["artifact_size_bytes"] = artifact.stat().st_size
    path.write_text(json.dumps(manifest))
    before = artifact.read_bytes(), path.read_bytes()
    with pytest.raises(ToolError) as error:
        build_judge_demo(output, force=True)
    assert error.value.code == "UNSAFE_JUDGE_REPLACEMENT"
    assert (artifact.read_bytes(), path.read_bytes()) == before


def test_mistaking_a_database_for_output_directory_is_rejected(tmp_path):
    database = tmp_path / "existing.rl"
    with GraphStore(database, read_only=False) as store:
        store.execute("CREATE (:UserNote {id:'preserve'})")
    before = database.read_bytes()
    with pytest.raises(ToolError) as error:
        build_judge_demo(database, force=True)
    assert error.value.code == "INVALID_JUDGE_OUTPUT"
    assert database.read_bytes() == before


def test_only_the_deliberate_judge_store_is_unignored():
    ignored = ["data/traceweaver.rl", "examples/judge-demo/private.rl"]
    for name in ignored:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", name], cwd=ROOT, capture_output=True, text=True
        )
        assert result.returncode == 0
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "examples/judge-demo/traceweaver-demo.rl"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    exceptions = [
        line for line in (ROOT / ".gitignore").read_text().splitlines() if line.startswith("!")
    ]
    assert exceptions == ["!examples/judge-demo/traceweaver-demo.rl"]
