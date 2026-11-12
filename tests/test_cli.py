import json
import subprocess
import sys


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "traceweaver", *map(str, args)],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_cli_seed_stats_context_and_errors(tmp_path):
    path = tmp_path / "cli.rl"
    for _ in range(2):
        result = run_cli("seed", "--database", path)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {"node_count": 21, "relationship_count": 27}
    result = run_cli("stats", "--database", path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["node_count"] == 21
    result = run_cli("context", "--incident", "INC-001", "--database", path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["context_paths"][0]["deployment_id"] == "DEP-001"
    result = run_cli("context", "--incident", "unknown", "--database", path)
    assert result.returncode == 3
    assert "Incident not found" in result.stderr
    result = run_cli("stats", "--database", tmp_path / "missing.rl")
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_configuration_environment_variable(database, monkeypatch):
    monkeypatch.setenv("TRACEWEAVER_DATABASE", str(database))
    result = run_cli("stats")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["relationship_count"] == 27
