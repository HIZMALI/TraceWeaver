import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from traceweaver.explanation_evaluation import evaluate_explanations, run_explanation_suite
from traceweaver.local_files import canonical_json
from traceweaver.tool_errors import ToolError

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "evaluation/explanation_cases.json"
GOLD = json.loads(SUITE.read_text(encoding="utf-8"))
SHA256 = "e716b63860712d9aaef23ac2b8a61b2bb77c225ce0359d8a36749cd65d2224cb"


def copy_case(tmp_path, index):
    data = deepcopy(GOLD)
    data["cases"] = [data["cases"][index]]
    path = tmp_path / "case.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize("index", range(19), ids=[c["case_id"] for c in GOLD["cases"]])
def test_frozen_explanation_scenario_uses_real_relate(tmp_path, index):
    result = run_explanation_suite(copy_case(tmp_path, index))
    assert result["passed"] == 1 and result["failed"] == 0, result["cases"][0]["failures"]
    assert result["metrics"]["adversarial_rejected"] == result["metrics"]["adversarial_attempted"]
    assert result["metrics"]["actual_graph_edges"] == result["metrics"]["expected_graph_edges"]


def test_suite_repeat_is_canonical_and_gold_not_rewritten(monkeypatch):
    import socket

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline evaluation must not contact the network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    before = SUITE.read_bytes()
    first, second = run_explanation_suite(SUITE), run_explanation_suite(SUITE)
    assert first["passed"] == 19 and first["failed"] == 0
    assert canonical_json(first) == canonical_json(second)
    assert SUITE.read_bytes() == before
    assert hashlib.sha256(before).hexdigest() == SHA256
    assert (
        first["metrics"]["reviewed_claims_correct"]
        == first["metrics"]["reviewed_claims_total"]
        == 32
    )
    assert (
        first["metrics"]["adversarial_rejected"] == first["metrics"]["adversarial_attempted"] == 133
    )
    assert first["metrics"]["abstention_required"] == first["metrics"]["abstention_observed"] == 1
    assert first["truncated_cases_excluded_from_completeness"] == ["X12", "X13"]
    assert first["whole_graph_completeness"] is None
    assert "traceweaver-explanation-eval-" not in canonical_json(first)


def test_wrong_gold_fails_and_cli_exit_is_nonzero(tmp_path):
    source = copy_case(tmp_path, 0)
    data = json.loads(source.read_bytes())
    data["cases"][0]["expected"]["required_claims"][0]["entity_ids"][0] = "FORGED-DEPLOYMENT"
    source.write_text(json.dumps(data), encoding="utf-8")
    output = tmp_path / "bad.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "evaluate-explanations",
            "--suite",
            str(source),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 14
    report = json.loads(output.read_bytes())
    assert report["failed"] == 1 and report["passed"] == 0
    assert any("FORGED-DEPLOYMENT" in f["check"] for f in report["cases"][0]["failures"])
    assert output.with_suffix(".md").is_file()
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == SHA256


def test_report_overwrite_is_explicit_and_protects_input_aliases(tmp_path):
    source = copy_case(tmp_path, 9)
    output = tmp_path / "out.json"
    result = evaluate_explanations(source, output)
    before = output.read_bytes()
    with pytest.raises(ToolError) as error:
        evaluate_explanations(source, output)
    assert error.value.code == "REPORT_EXISTS"
    assert output.read_bytes() == before
    assert evaluate_explanations(source, output, overwrite=True) == result
    alias = tmp_path / "alias.json"
    alias.hardlink_to(source)
    with pytest.raises(ToolError) as error:
        evaluate_explanations(source, alias, overwrite=True)
    assert error.value.code == "INVALID_REPORT_PATH"


def test_untrusted_profile_cannot_supply_path_or_query(tmp_path):
    source = copy_case(tmp_path, 0)
    data = json.loads(source.read_bytes())
    data["cases"][0]["profiles"] = ["../private.rl"]
    source.write_text(json.dumps(data))
    with pytest.raises(ToolError) as error:
        run_explanation_suite(source)
    assert error.value.code == "INVALID_EXPLANATION_SUITE"
