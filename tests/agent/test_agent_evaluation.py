import hashlib
import json
from pathlib import Path

import pytest

from traceweaver.agent_evaluation import evaluate_agent, main

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "evaluation/sprint06_agent_cases.json"


def test_frozen_agent_gold_bytes_match_checkout_digest():
    expected = (SUITE.with_suffix(".sha256")).read_text().split()[0]
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == expected
    assert len(json.loads(SUITE.read_bytes())["cases"]) == 35


def test_new_agent_suite_executes_isolated_real_tools_and_controlled_protocol():
    report = evaluate_agent(SUITE)
    assert report["total"] == 35 and report["failed"] == 0
    assert report["native_cases"] == 18 and report["protocol_cases"] == 17
    assert report["native_edge_agreement"]["denominator"] > 0
    assert report["canonical_repeatability"]["denominator"] == 18
    assert report["live_model_accuracy"] is None and not report["source_truth_verified"]
    assert all(c["status"] == "PASS" for c in report["cases"])


def test_corrupted_independent_gold_returns_nonzero_without_rewriting_original(tmp_path):
    before = SUITE.read_bytes()
    corrupt = json.loads(before)
    corrupt["cases"][0]["gold"]["edge"][1] = "SYNTHETIC-INCORRECT-ENDPOINT"
    source, output = tmp_path / "bad-gold.json", tmp_path / "report.json"
    source.write_text(json.dumps(corrupt), encoding="utf8")
    assert main(["--suite", str(source), "--output", str(output)]) == 15
    report = json.loads(output.read_bytes())
    assert report["failed"] == 1 and report["cases"][0]["code"] == "GOLD_NATIVE_EDGE"
    assert SUITE.read_bytes() == before


def test_agent_evaluation_never_overwrites_an_existing_report_without_opt_in(tmp_path):
    output = tmp_path / "report.json"
    output.write_bytes(b"owned preexisting report")
    with pytest.raises(SystemExit) as failure:
        main(["--suite", str(SUITE), "--output", str(output)])
    assert failure.value.code == 2 and output.read_bytes() == b"owned preexisting report"


def test_malformed_agent_gold_fails_safely_without_echoing_input(tmp_path, capsys):
    source, output = tmp_path / "invalid.json", tmp_path / "report.json"
    source.write_bytes(b'{"private_input":"do-not-disclose"}')
    assert main(["--suite", str(source), "--output", str(output)]) == 15
    assert "do-not-disclose" not in capsys.readouterr().out and not output.exists()


def test_evaluation_output_cannot_alias_gold_even_with_overwrite_opt_in(tmp_path):
    source = tmp_path / "gold.json"
    before = SUITE.read_bytes()
    source.write_bytes(before)
    assert main(["--suite", str(source), "--output", str(source), "--overwrite"]) == 15
    assert source.read_bytes() == before
