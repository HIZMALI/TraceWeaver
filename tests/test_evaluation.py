import hashlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from traceweaver.evaluation import evaluate_to_files, run_suite
from traceweaver.local_files import canonical_json
from traceweaver.tool_errors import ToolError

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evaluation/cases.json"
GOLD = json.loads(SUITE.read_text(encoding="utf-8"))
FROZEN_SHA256 = "6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8"


def single_suite(tmp_path, index):
    data = deepcopy(GOLD)
    data["cases"] = [data["cases"][index]]
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize("index", range(20), ids=[case["case_id"] for case in GOLD["cases"]])
def test_frozen_synthetic_scenario_on_real_relate(tmp_path, index):
    result = run_suite(single_suite(tmp_path, index))
    assert result["scenarios_executed"] == result["passed"] == 1
    assert result["failed"] == 0, result["cases"][0]["failures"]
    assert result["cases"][0]["diagnostics"]["investigation_query_count"] <= 6
    assert result["causal_conclusion"] == "NOT_ESTABLISHED"


def test_canonical_evaluation_is_byte_deterministic_and_gold_not_rewritten(monkeypatch):
    def network_forbidden(*args, **kwargs):
        raise AssertionError("Evaluation must be offline")

    monkeypatch.setattr(socket, "getaddrinfo", network_forbidden)
    monkeypatch.setattr(socket.socket, "connect", network_forbidden)
    before = hashlib.sha256(SUITE.read_bytes()).hexdigest()
    first, second = run_suite(SUITE), run_suite(SUITE)
    assert canonical_json(first) == canonical_json(second)
    assert first["passed"] == 20 and first["failed"] == 0
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == before == FROZEN_SHA256
    assert "traceweaver-evaluation-" not in canonical_json(first)
    assert (
        max(case["diagnostics"]["max_observed_services_per_evidence"] for case in first["cases"])
        == 100
    )
    candidate = first["metrics"]["candidate_retrieval"]
    assert candidate["true_positive"] == candidate["expected_count"] == 53
    assert candidate["false_positive"] == candidate["false_negative"] == 0
    assert candidate["included_case_count"] == 18 and candidate["excluded_truncated_cases"] == 2
    assert first["metrics"]["evidence_scope"]["expected_count"] == 61
    assert first["metrics"]["conflict_detection"]["expected_count"] == 3
    assert first["metrics"]["temporal"] == {"correct": 120, "total": 120, "agreement": 1.0}
    assert first["metrics"]["graph_edges"] == {"correct": 432, "total": 432, "agreement": 1.0}


def test_empty_denominators_are_null_not_perfect_accuracy(tmp_path):
    result = run_suite(single_suite(tmp_path, 11))  # E12 has no candidates/evidence.
    metric = result["metrics"]["candidate_retrieval"]
    assert metric["expected_count"] == metric["predicted_count"] == 0
    assert metric["precision"] is None and metric["recall"] is None
    assert metric["undefined_precision_cases"] == metric["undefined_recall_cases"] == 1
    assert result["metrics"]["temporal"]["agreement"] is None


def test_false_gold_produces_exact_failures_and_nonzero_cli_exit(tmp_path):
    source = single_suite(tmp_path, 0)
    data = json.loads(source.read_text())
    data["cases"][0]["expected"]["candidates"][0]["temporal_classification"] = "AFTER"
    source.write_text(json.dumps(data))
    output = tmp_path / "failed-report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "evaluate",
            "--suite",
            str(source),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 11
    report = json.loads(output.read_text())
    assert report["failed"] == 1 and report["passed"] == 0
    assert any(
        f["check"].endswith("temporal_classification")
        and f["expected"] == "AFTER"
        and f["actual"] == "BEFORE"
        for f in report["cases"][0]["failures"]
    )
    assert output.with_suffix(".md").is_file()
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == FROZEN_SHA256


def test_report_overwrite_is_explicit_and_never_overwrites_suite(tmp_path):
    source = single_suite(tmp_path, 11)
    output = tmp_path / "report.json"
    first = evaluate_to_files(source, output)
    before = output.read_bytes()
    with pytest.raises(ToolError) as error:
        evaluate_to_files(source, output)
    assert error.value.code == "REPORT_EXISTS"
    assert output.read_bytes() == before
    assert evaluate_to_files(source, output, overwrite=True) == first
    assert output.read_bytes() == before
    with pytest.raises(ToolError) as error:
        evaluate_to_files(source, source, overwrite=True)
    assert error.value.code == "INVALID_REPORT_PATH"


def test_untrusted_fixture_profile_is_not_a_filesystem_or_query_hook(tmp_path):
    source = single_suite(tmp_path, 0)
    data = json.loads(source.read_text())
    data["cases"][0]["fixture_profiles"] = ["../private-store.rl"]
    source.write_text(json.dumps(data))
    with pytest.raises(ToolError) as error:
        run_suite(source)
    assert error.value.code == "INVALID_EVALUATION_SUITE"


def test_report_cannot_overwrite_suite_through_a_hard_link(tmp_path):
    source = single_suite(tmp_path, 11)
    output = tmp_path / "alias-report.json"
    output.hardlink_to(source)
    before = source.read_bytes()
    with pytest.raises(ToolError) as error:
        evaluate_to_files(source, output, overwrite=True)
    assert error.value.code == "INVALID_REPORT_PATH"
    assert source.read_bytes() == output.read_bytes() == before
