"""Validate release tooling at its artifact and native boundaries, not screenshots as gold."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def capture(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "release_capture_tests", ROOT / "scripts/capture_release.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_caption_time_does_not_use_wall_clock_or_approximate_runner_start(capture):
    assert capture.subtitle_time(62.31) == "0:01:02.31"
    assert capture.subtitle_time(115) == "0:01:55.00"


def test_captions_require_measured_ordered_real_scene_cues(capture):
    cues = [{"seconds": n * 11 + 0.7, "caption": "Actual native evidence"} for n in range(10)]
    text = capture.captions(cues)
    assert "EXPLANATORY CAPTIONS" in text
    assert "0:00:00.70,0:00:11.70" in text
    assert "0:01:55.00" in text
    cues[1]["seconds"] = 0
    with pytest.raises(ValueError):
        capture.captions(cues)


@pytest.mark.parametrize("caption", ["{override}", "hidden\\command", "two\nlines"])
def test_caption_injection_is_rejected(capture, caption):
    cues = [{"seconds": n * 11, "caption": "Actual evidence"} for n in range(10)]
    cues[0]["caption"] = caption
    with pytest.raises(ValueError):
        capture.captions(cues)


def test_documented_direction_query_runs_on_intact_real_relate():
    from traceweaver.storage import GraphStore

    with GraphStore(ROOT / "examples/judge-demo/traceweaver-demo.rl", read_only=True) as store:
        rows = store.execute(
            "MATCH (i:Incident {id: $incident_id})-[:AFFECTS]->(s:Service) "
            "MATCH (s)-[:DEPENDS_ON]->(a:Service)<-[:TARGETS]-(d:Deployment) "
            "MATCH (d)-[:INCLUDES_CHANGE]->(c:Change) "
            "RETURN i.id, s.id, a.id, d.id, c.id LIMIT 10",
            {"incident_id": "INC-001"},
        )
    assert [list(r.values()) for r in rows] == [
        ["INC-001", "SVC-PAYMENT", "SVC-AUTH", "DEP-001", "CHG-001"]
    ]


def test_package_builder_refuses_overwrite_before_opening_any_store(tmp_path):
    import subprocess

    (tmp_path / "traceweaver-sentinel.whl").write_bytes(b"owner artifact")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_judge_wheel.py"), "--output", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 2
    assert (tmp_path / "traceweaver-sentinel.whl").read_bytes() == b"owner artifact"
