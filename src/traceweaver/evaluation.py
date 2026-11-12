"""Reproducible, offline synthetic evaluation through the unchanged investigation service."""

import hashlib
import tempfile
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from pydantic import ValidationError

from traceweaver.evaluation_models import EvaluationSuite
from traceweaver.investigation import investigate
from traceweaver.local_files import (
    canonical_json,
    local_path,
    parse_json_document,
    read_local_bytes,
)
from traceweaver.queries import IncidentNotFound
from traceweaver.seed import seed_database
from traceweaver.storage import GraphStore, StorageError
from traceweaver.tool_errors import ToolError

FIXTURE_PROFILES = {
    "baseline": "demo_incidents.json",
    "sprint01": "sprint01_cases.json",
    "evaluation": "evaluation_cases.json",
    "caps": "evaluation_caps.json",
}


class CountingStore(GraphStore):
    calls = 0

    def execute(self, *args, **kwargs):
        self.calls += 1
        return super().execute(*args, **kwargs)


def retrieval_metric(predicted: set, expected: set) -> dict:
    return {
        "true_positive": len(predicted & expected),
        "false_positive": len(predicted - expected),
        "false_negative": len(expected - predicted),
        "predicted_count": len(predicted),
        "expected_count": len(expected),
        "undefined_precision_cases": int(not predicted),
        "undefined_recall_cases": int(not expected),
    }


def _final_metric(items: list[dict | None], unit: str) -> dict:
    eligible = [item for item in items if item is not None]
    result = {key: sum(item[key] for item in eligible) for key in retrieval_metric(set(), set())}
    result.update(
        unit=unit,
        included_case_count=len(eligible),
        excluded_truncated_cases=len(items) - len(eligible),
        precision=result["true_positive"] / result["predicted_count"]
        if result["predicted_count"]
        else None,
        recall=result["true_positive"] / result["expected_count"]
        if result["expected_count"]
        else None,
    )
    return result


def _graph_validity(store: GraphStore, result) -> tuple[dict, int]:
    paths = [path for c in result.candidates for path in c.graph_paths]
    paths += [change.graph_path for c in result.candidates for change in c.changes]
    paths += [path for evidence in result.evidence for path in evidence.graph_paths]
    edge_keys = set()
    valid_layout = True
    for path in paths:
        valid_layout &= len(path.node_ids) == len(path.edges) + 1
        for index, edge in enumerate(path.edges):
            source, target = path.node_ids[index : index + 2]
            if edge.traversal_direction == "REVERSE":
                source, target = target, source
            valid_layout &= (source, target) == (edge.source_id, edge.target_id)
            edge_keys.add((edge.type, edge.source_id, edge.target_id))
    # Investigation caps imply at most 800 distinct returned edges for the current schema.
    if len(edge_keys) > 1000:
        raise ToolError(
            "EVALUATION_GRAPH_CAP", "Returned edge validation exceeds its bounded contract."
        )
    edges = [
        {"key": str(index), "type": key[0], "source_id": key[1], "target_id": key[2]}
        for index, key in enumerate(sorted(edge_keys))
    ]
    found = (
        store.execute(
            "UNWIND $edges AS e MATCH (a)-[r]->(b) "
            "WHERE a.id=e.source_id AND b.id=e.target_id AND type(r)=e.type "
            "RETURN DISTINCT e.key AS key LIMIT $limit",
            {"edges": edges, "limit": 1001},
        )
        if edges
        else []
    )
    return {
        "path_layout_valid": bool(valid_layout),
        "expected_edge_count": len(edges),
        "actual_edge_count": len(found),
    }, len(paths)


def _compare(case, result, graph, queries) -> tuple[dict, dict]:
    failures = []
    assertion_count = failure_count = 0

    def check(name, actual, expected):
        nonlocal assertion_count, failure_count
        assertion_count += 1
        if actual != expected:
            failure_count += 1
            if len(failures) < 100:
                failures.append({"check": name, "expected": expected, "actual": actual})

    gold = case.expected
    actual_candidates = {(c.deployment_id, c.target_service_id): c for c in result.candidates}
    expected_candidates = {(c.deployment_id, c.target_service_id): c for c in gold.candidates}
    actual_evidence = {e.evidence_id: e for e in result.evidence}
    expected_evidence = {e.evidence_id: e for e in gold.evidence}
    conflicts = {
        tuple(sorted(c.evidence_ids))
        for c in result.contradictions
        if c.classification == "CONFLICTING_OBSERVATIONS"
    }
    undetermined = {
        tuple(sorted(c.evidence_ids))
        for c in result.contradictions
        if c.classification == "UNDETERMINED"
    }
    expected_conflicts = {tuple(sorted(pair)) for pair in gold.conflict_pairs}
    expected_undetermined = {tuple(sorted(pair)) for pair in gold.undetermined_pairs}
    check("incident_id", result.incident_id, case.incident_id)
    check("causal_conclusion", result.causal_conclusion, "NOT_ESTABLISHED")
    check("synthetic_marker", result.is_demo, True)
    check("candidate_identities", sorted(actual_candidates), sorted(expected_candidates))
    check("candidate_duplicates", len(actual_candidates), len(result.candidates))
    check("evidence_membership", sorted(actual_evidence), sorted(expected_evidence))
    check("evidence_duplicates", len(actual_evidence), len(result.evidence))
    temporal_correct = provenance_correct = 0
    for key, expected in expected_candidates.items():
        actual = actual_candidates.get(key)
        prefix = f"candidate:{key[0]}/{key[1]}"
        for field in (
            "dependency_depth",
            "temporal_classification",
            "candidate_assessment",
            "change_ids",
        ):
            check(prefix + ":" + field, getattr(actual, field, None), getattr(expected, field))
        check(
            prefix + ":event_utc",
            actual.deployment_occurred_at.utc if actual else None,
            expected.event_utc,
        )
        check(
            prefix + ":graph_path",
            actual.graph_paths[0].model_dump() if actual else None,
            expected.graph_path.model_dump(),
        )
        temporal_correct += int(
            actual is not None
            and actual.temporal_classification == expected.temporal_classification
        )
    for key, expected in expected_evidence.items():
        actual = actual_evidence.get(key)
        prefix = "evidence:" + key
        for field in (
            "temporal_classification",
            "provenance_status",
            "verification_status",
            "observed_service_ids",
        ):
            check(prefix + ":" + field, getattr(actual, field, None), getattr(expected, field))
        check(
            prefix + ":event_utc",
            actual.evidence_observed_at.utc if actual else None,
            expected.event_utc,
        )
        check(
            prefix + ":warning_codes",
            sorted(w.code for w in actual.warnings) if actual else None,
            sorted(expected.warning_codes),
        )
        temporal_correct += int(
            actual is not None
            and actual.temporal_classification == expected.temporal_classification
        )
        provenance_correct += int(
            actual is not None
            and actual.provenance_status == expected.provenance_status
            and actual.verification_status == expected.verification_status
            and sorted(w.code for w in actual.warnings) == sorted(expected.warning_codes)
        )
    check("conflict_pairs", sorted(conflicts), sorted(expected_conflicts))
    check("undetermined_pairs", sorted(undetermined), sorted(expected_undetermined))
    check(
        "not_evaluable_count",
        result.contradiction_audit.not_evaluable_count,
        gold.not_evaluable_count,
    )
    check("investigation_status", result.investigation_status, gold.investigation_status)
    check("truncation", result.truncation, gold.truncation.model_dump())
    check(
        "truncation_or", result.results_may_be_truncated, any(gold.truncation.model_dump().values())
    )
    present_codes = {item.code for item in result.limitations}
    for code in gold.required_limitation_codes:
        check("limitation:" + code, code in present_codes, True)
    audit = result.provenance_audit
    check("audit_scope", audit.scope, "RETURNED_EVIDENCE")
    check("audit_total", audit.total_evidence, len(result.evidence))
    check(
        "audit_exclusive_counts",
        audit.traceable_count + audit.incomplete_count + audit.invalid_count,
        audit.total_evidence,
    )
    check("actual_graph_edge_count", graph["actual_edge_count"], graph["expected_edge_count"])
    check("actual_graph_path_layout", graph["path_layout_valid"], True)
    check("bounded_investigation_query_count", queries <= 6, True)
    check(
        "all_lists_bounded",
        max(
            len(result.candidates),
            len(result.evidence),
            len(result.timeline),
            len(result.contradictions),
        )
        <= 100,
        True,
    )
    metrics = {
        "candidate_retrieval": None
        if gold.truncation.candidates
        else retrieval_metric(set(actual_candidates), set(expected_candidates)),
        "evidence_scope": None
        if gold.truncation.evidence
        else retrieval_metric(set(actual_evidence), set(expected_evidence)),
        "conflict_detection": None
        if (
            gold.truncation.evidence
            or gold.truncation.observations
            or gold.truncation.contradictions
        )
        else retrieval_metric(conflicts, expected_conflicts),
        "temporal": {
            "correct": temporal_correct,
            "total": len(gold.candidates) + len(gold.evidence),
        },
        "provenance": {"correct": provenance_correct, "total": len(gold.evidence)},
        "graph_edges": {
            "correct": graph["actual_edge_count"],
            "total": graph["expected_edge_count"],
        },
    }
    return {
        "case_id": case.case_id,
        "passed": failure_count == 0,
        "assertion_count": assertion_count,
        "failure_count": failure_count,
        "failures": failures,
        "failures_may_be_truncated": failure_count > len(failures),
        "diagnostics": {
            "investigation_query_count": queries,
            "returned_candidates": len(result.candidates),
            "returned_evidence": len(result.evidence),
            "returned_timeline": len(result.timeline),
            "max_observed_services_per_evidence": max(
                (len(e.observed_service_ids) for e in result.evidence), default=0
            ),
            "max_changes_per_candidate": max(
                (len(c.changes) for c in result.candidates), default=0
            ),
        },
    }, metrics


def run_suite(path: str | Path) -> dict:
    raw = read_local_bytes(path)
    try:
        suite = EvaluationSuite.model_validate(parse_json_document(raw, max_depth=16))
    except ValidationError:
        raise ToolError(
            "INVALID_EVALUATION_SUITE", "Evaluation suite contract validation failed."
        ) from None
    if version("relate-db") != "1.0.0":
        raise ToolError("UNSUPPORTED_ENGINE", "Evaluation requires relate-db 1.0.0.")
    results, metrics = [], []
    for case in suite.cases:
        with tempfile.TemporaryDirectory(prefix="traceweaver-evaluation-") as temp:
            database = Path(temp) / "case.rl"
            for profile in case.fixture_profiles:
                fixture = files("traceweaver").joinpath("fixtures", FIXTURE_PROFILES[profile])
                seed_database(database, fixture)
            with CountingStore(database) as store:
                before = store.calls
                try:
                    result = investigate(store, case.incident_id, case.options)
                except (IncidentNotFound, StorageError):
                    raise ToolError(
                        "EVALUATION_EXECUTION_ERROR",
                        "A curated evaluation case could not execute.",
                        11,
                    ) from None
                count = store.calls - before
                graph, _ = _graph_validity(store, result)
                case_result, case_metrics = _compare(case, result, graph, count)
                results.append(case_result)
                metrics.append(case_metrics)
    totals = {}
    for key, unit in [
        ("candidate_retrieval", "scenario_deployment_target_pairs"),
        ("evidence_scope", "scenario_evidence_ids"),
        ("conflict_detection", "scenario_unordered_conflict_pairs"),
    ]:
        totals[key] = _final_metric([item[key] for item in metrics], unit)
    for key in ("temporal", "provenance", "graph_edges"):
        correct = sum(item[key]["correct"] for item in metrics)
        total = sum(item[key]["total"] for item in metrics)
        totals[key] = {
            "correct": correct,
            "total": total,
            "agreement": correct / total if total else None,
        }
    return {
        "evaluation_contract_version": "1.0",
        "suite_id": suite.suite_id,
        "suite_sha256": hashlib.sha256(raw).hexdigest(),
        "relate_version": "1.0.0",
        "synthetic_only": True,
        "external_verification_status": "NOT_PERFORMED",
        "causal_conclusion": "NOT_ESTABLISHED",
        "scenarios_executed": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "cases": results,
        "metrics": totals,
        "interpretation": (
            "Synthetic retrieval/path/state agreement, not root-cause accuracy. "
            "Truncated scenarios are excluded from affected retrieval metrics."
        ),
    }


def markdown_report(result: dict) -> str:
    lines = [
        "# TraceWeaver offline synthetic evaluation",
        "",
        f"Suite: `{result['suite_id']}`",
        "",
        f"Scenarios: {result['scenarios_executed']}; "
        f"passed: {result['passed']}; failed: {result['failed']}.",
        "",
        "Causation: NOT_ESTABLISHED. External verification: NOT_PERFORMED.",
        "",
        "These are synthetic relevance/path metrics, not root-cause accuracy.",
        "",
        "| Case | Result | Assertions | Failures |",
        "| --- | --- | ---: | ---: |",
    ]
    for case in result["cases"]:
        lines.append(
            f"| {case['case_id']} | {'PASS' if case['passed'] else 'FAIL'} "
            f"| {case['assertion_count']} | {case['failure_count']} |"
        )
        for failure in case["failures"]:
            lines.append(
                f"\nFailure: `{failure['check']}`; "
                f"expected `{failure['expected']}`, actual `{failure['actual']}`.\n"
            )
    lines += [
        "",
        "## Metrics and denominators",
        "",
        "```json",
        canonical_json(result["metrics"]).rstrip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def evaluate_to_files(suite: str | Path, output: str | Path, *, overwrite: bool = False) -> dict:
    suite_path = local_path(suite, must_exist=True)
    output_path = local_path(output)
    markdown_path = output_path.with_suffix(".md")
    if output_path.suffix != ".json" or suite_path in {output_path, markdown_path}:
        raise ToolError("INVALID_REPORT_PATH", "Select a separate .json report output.")
    for path in (output_path, markdown_path):
        local_path(path)
        if path.exists() and path.samefile(suite_path):
            raise ToolError("INVALID_REPORT_PATH", "Report output must not alias the input suite.")
        if path.exists() and not overwrite:
            raise ToolError(
                "REPORT_EXISTS", "Report output exists; explicit --overwrite is required."
            )
    result = run_suite(suite_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    try:
        for path, text in [
            (output_path, canonical_json(result)),
            (markdown_path, markdown_report(result)),
        ]:
            with path.open(mode, encoding="utf-8", newline="\n") as destination:
                destination.write(text)
    except OSError:
        raise ToolError(
            "REPORT_WRITE_ERROR", "Cannot write the selected evaluation report.", 1
        ) from None
    return result
