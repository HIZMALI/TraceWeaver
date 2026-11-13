import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def study():
    source = Path(__file__).resolve().parents[2] / "evaluation/graph-vs-flat/run_study.py"
    spec = importlib.util.spec_from_file_location("retrieval_study", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_metric_empty_denominators_and_false_positive(study):
    assert study.metrics([], []) == {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "precision": None,
        "recall": None,
        "exact": True,
    }
    assert study.metrics(["unrelated"], ["expected"])["fp"] == 1
    assert study.metrics(["unrelated"], ["expected"])["fn"] == 1


def test_flat_index_retains_directed_edge_information_and_missing_anchor_guard(study):
    nodes = [
        {"label": "Incident", "properties": {"id": "I"}},
        {"label": "Deployment", "properties": {"id": "D"}},
    ]
    edges = [{"source": "I", "target": "D", "type": "UNIT_DIRECTED_FACT"}]
    index = study.FlatIndex(nodes, edges)
    assert all(token in index.documents["D"] for token in ("unit", "directed", "fact"))
    assert index.search(
        {
            "incident": "I",
            "label": "Deployment",
            "operation": "candidates",
            "question": "D UNIT_DIRECTED_FACT",
        }
    ) == ["D"]
    assert (
        index.search(
            {
                "incident": "MISSING",
                "label": "Deployment",
                "operation": "candidates",
                "question": "D UNIT_DIRECTED_FACT",
            }
        )
        == []
    )


def test_frozen_study_uses_real_native_edges_and_exposes_gold_erratum(study):
    report = study.run_study()
    assert report["native_counts"] == {"node_count": 51, "relationship_count": 67}
    cases = {c["id"]: c for c in report["cases"]}
    assert len(cases) == 14
    # Preserve the erroneous frozen expectation and report its actual mismatch; see ERRATA.md.
    assert cases["R13"]["expected_ids"] == ["DEP-002"]
    assert cases["R13"]["graph"]["ids"] == ["DEP-001"]
    assert cases["R13"]["graph"]["metrics"]["exact"] is False
    assert cases["R13"]["graph"]["expected_cap_matches"] is True
    assert all(c["graph"]["metrics"]["exact"] for key, c in cases.items() if key != "R13")
    assert cases["R01"]["graph"]["matched_native_edges"]
    assert cases["R12"]["graph"]["metrics"]["precision"] is None
