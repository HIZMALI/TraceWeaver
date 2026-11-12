"""Full legacy responses captured from real Relate using commit e504012's source."""

import json
import subprocess
import sys
from pathlib import Path


def snapshot():
    return json.loads((Path(__file__).parent / "snapshots/sprint00_api.json").read_text())


def test_legacy_http_responses_match_original_commit(client):
    for endpoint, expected in snapshot().items():
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.json() == expected


def test_legacy_cli_json_matches_original_contract(database):
    for command in ["stats", "context"]:
        arguments = [sys.executable, "-m", "traceweaver", command, "--database", str(database)]
        if command == "context":
            arguments += ["--incident", "INC-001"]
        result = subprocess.run(arguments, capture_output=True, text=True, check=True, timeout=30)
        expected = (
            {"node_count": 21, "relationship_count": 27}
            if command == "stats"
            else snapshot()["/incidents/INC-001/context"]
        )
        assert json.loads(result.stdout) == expected
