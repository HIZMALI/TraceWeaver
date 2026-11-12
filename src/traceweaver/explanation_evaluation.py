"""Frozen explanation gold, semantic firewall attacks, and actual Relate edge checks."""

import hashlib
import json
import tempfile
from importlib.metadata import version
from typing import Annotated, Literal

from pydantic import Field, ValidationError

from traceweaver.citation_validator import CitationRejected, CitationValidator
from traceweaver.explanation import explain_investigation
from traceweaver.explanation_catalog import build_catalog
from traceweaver.explanation_models import Claim, ClaimType, Identity, StrictModel
from traceweaver.explanation_scenarios import seed_explanation_profile
from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.local_files import (
    canonical_json,
    local_path,
    parse_json_document,
    read_local_bytes,
)
from traceweaver.model_selection import accept_proposal
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError


class ExpectedClaim(StrictModel):
    claim_type: ClaimType
    entity_ids: Annotated[list[Identity], Field(min_length=1, max_length=12)]
    node_ids: Annotated[list[Identity], Field(max_length=7)] | None = None
    event_utc: Annotated[str, Field(max_length=40)] | None = None
    temporal_classification: (
        Literal["BEFORE", "AT_ONSET", "AFTER", "OUTSIDE_WINDOW", "UNKNOWN"] | None
    ) = None
    provenance_status: Literal["TRACEABLE", "INCOMPLETE", "INVALID"] | None = None
    verification_status: Literal["SYNTHETIC", "UNVERIFIED_EXTERNAL", "NOT_AVAILABLE"] | None = None


class ExpectedExplanation(StrictModel):
    status: Literal["EXPLAINED", "PARTIAL_CONTEXT", "ABSTAINED"]
    required_claims: Annotated[list[ExpectedClaim], Field(max_length=100)]
    forbidden_claim_types: Annotated[list[ClaimType], Field(max_length=11)]
    required_uncertainty_codes: Annotated[list[Identity], Field(max_length=20)]
    truncated: bool
    expected_evidence_ids: Annotated[list[Identity], Field(max_length=100)] | None = None
    conflicts: Annotated[int, Field(ge=0)] | None = None
    undetermined: Annotated[int, Field(ge=0)] | None = None
    forbidden_entity_ids: Annotated[list[Identity], Field(max_length=20)] = Field(
        default_factory=list
    )
    forbidden_output_fragments: Annotated[
        list[Annotated[str, Field(max_length=128)]], Field(max_length=20)
    ] = Field(default_factory=list)


class ExplanationCase(StrictModel):
    case_id: Annotated[str, Field(pattern=r"^X[0-9]{2}$")]
    incident_id: Identity
    profiles: Annotated[
        list[
            Literal[
                "baseline", "sprint01", "evaluation", "caps", "adversarial", "external", "ready"
            ]
        ],
        Field(min_length=1, max_length=4),
    ]
    options: InvestigationOptions
    expected: ExpectedExplanation


class ExplanationSuite(StrictModel):
    contract_version: Literal["1.0"]
    suite_id: Identity
    cases: Annotated[list[ExplanationCase], Field(min_length=1, max_length=64)]


def adversarial_checks(investigation, catalog) -> list[dict]:
    """Controlled hostile proposals, never model/runtime evidence."""
    first = catalog.claims[0]
    snapshot = catalog.investigation_fingerprint
    attacks = []

    def rejected(name, operation):
        try:
            operation()
        except (CitationRejected, ValidationError):
            attacks.append({"name": name, "rejected": True})
        else:
            attacks.append({"name": name, "rejected": False})

    validator = CitationValidator(investigation, catalog)
    rejected(
        "unknown_claim",
        lambda: validator.validate(["C-" + "0" * 24], snapshot, require_caution=False),
    )
    rejected(
        "duplicate_id",
        lambda: validator.validate([first.claim_id] * 2, snapshot, require_caution=False),
    )
    rejected(
        "cross_snapshot",
        lambda: validator.validate([first.claim_id], "0" * 64, require_caution=False),
    )

    def forged_claim(data):
        altered = catalog.model_copy(deep=True)
        altered.claims[0] = Claim.model_validate(data)
        return CitationValidator(investigation, altered).validate(
            [altered.claims[0].claim_id], snapshot, require_caution=False
        )

    data = first.model_dump()
    data["statement"] = "A connected deployment is the confirmed root cause."
    rejected("forged_statement", lambda: forged_claim(data))
    path_claim = next((c for c in catalog.claims if any(p.graph_path for p in c.citations)), None)
    if path_claim:

        def direction_attack():
            altered = catalog.model_copy(deep=True)
            data = path_claim.model_dump()
            proof = next(c for c in data["citations"] if c["graph_path"])
            proof["graph_path"]["edges"][-1]["traversal_direction"] = (
                "REVERSE"
                if proof["graph_path"]["edges"][-1]["traversal_direction"] == "FORWARD"
                else "FORWARD"
            )
            altered.claims[0] = Claim.model_validate(data)
            return CitationValidator(investigation, altered).validate(
                [path_claim.claim_id], snapshot, require_caution=False
            )

        rejected("forged_edge_direction", direction_attack)
    proposal = {
        "investigation_fingerprint": snapshot,
        "selected_claim_ids": [first.claim_id],
        "focus": "BALANCED",
        "abstain": False,
        "causal_conclusion": "ESTABLISHED",
    }
    rejected(
        "model_extra_causal_field",
        lambda: accept_proposal(json.dumps(proposal).encode(), investigation, catalog),
    )
    proposal2 = {
        "investigation_fingerprint": snapshot,
        "selected_claim_ids": ["C-" + "0" * 24],
        "focus": "BALANCED",
        "abstain": False,
    }
    rejected(
        "model_forged_id",
        lambda: accept_proposal(json.dumps(proposal2).encode(), investigation, catalog),
    )
    return attacks


def _case(database, case):
    for profile in case.profiles:
        seed_explanation_profile(database, profile)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with GraphStore(database) as store:
        investigation = investigate(store, case.incident_id, case.options)
        catalog = build_catalog(investigation)
        validator = CitationValidator(investigation, catalog)
        validated = []
        for start in range(0, len(catalog.claims), 10):
            validated += validator.validate(
                [c.claim_id for c in catalog.claims[start : start + 10]],
                catalog.investigation_fingerprint,
                require_caution=False,
            )
        edges = sorted(
            {
                (edge.type, edge.source_id, edge.target_id)
                for claim in catalog.claims
                for citation in claim.citations
                if citation.graph_path
                for edge in citation.graph_path.edges
            }
        )
        if len(edges) > 1000:
            raise ToolError("EXPLANATION_EDGE_LIMIT", "Evaluation edge validation cap exceeded.")
        rows = (
            store.execute(
                "UNWIND $edges AS e MATCH (a)-[r]->(b) "
                "WHERE a.id=e.source AND b.id=e.target AND type(r)=e.type "
                "RETURN DISTINCT e.key AS key LIMIT 1001",
                {
                    "edges": [
                        {"key": str(n), "type": edge[0], "source": edge[1], "target": edge[2]}
                        for n, edge in enumerate(edges)
                    ]
                },
            )
            if edges
            else []
        )
    report = explain_investigation(investigation)
    second = explain_investigation(investigation)
    attacks = adversarial_checks(investigation, catalog)
    checks = []

    def check(name, actual, expected):
        checks.append(
            {"check": name, "passed": actual == expected, "expected": expected, "actual": actual}
        )

    gold = case.expected
    check("status", report.explanation_status, gold.status)
    check("offline_label", report.ai_generated_selection, False)
    check("mode", report.mode_executed, "DETERMINISTIC")
    check("causal_conclusion", report.causal_conclusion, "NOT_ESTABLISHED")
    check(
        "mandatory_caution", any(c.claim_type == "NO_CAUSAL_VERDICT" for c in report.claims), True
    )
    check("canonical_repeat", report.model_dump_json() == second.model_dump_json(), True)
    check("truncation", any(report.truncation.investigation.values()), gold.truncated)
    check("file_immutable", hashlib.sha256(database.read_bytes()).hexdigest() == before, True)
    check("actual_stored_edges", len(rows), len(edges))
    check("all_catalog_validated", len(validated), len(catalog.claims))
    codes = {u.code for u in report.uncertainties}
    for code in gold.required_uncertainty_codes:
        check("uncertainty:" + code, code in codes, True)
    required_correct = 0
    for expected in gold.required_claims:
        match = next(
            (
                c
                for c in catalog.claims
                if c.claim_type == expected.claim_type
                and c.referenced_entity_ids == expected.entity_ids
            ),
            None,
        )
        valid = match is not None
        if match:
            for field in (
                "event_utc",
                "temporal_classification",
                "provenance_status",
                "verification_status",
            ):
                value = getattr(expected, field)
                if value is not None:
                    valid &= any(getattr(c, field) == value for c in match.citations)
            if expected.node_ids is not None:
                valid &= any(
                    c.graph_path and c.graph_path.node_ids == expected.node_ids
                    for c in match.citations
                )
        check(
            "reviewed_claim:" + expected.claim_type + ":" + "/".join(expected.entity_ids),
            bool(valid),
            True,
        )
        required_correct += int(bool(valid))
    kinds = {c.claim_type for c in catalog.claims}
    for kind in gold.forbidden_claim_types:
        check("forbidden_kind:" + kind, kind in kinds, False)
    ids = {value for c in catalog.claims for value in c.referenced_entity_ids}
    for identity in gold.forbidden_entity_ids:
        check("forbidden_identity:" + identity, identity in ids, False)
    if gold.expected_evidence_ids is not None:
        check(
            "incident_scoped_evidence",
            sorted(e.evidence_id for e in investigation.evidence),
            sorted(gold.expected_evidence_ids),
        )
    for field in ("conflicts", "undetermined"):
        value = getattr(gold, field)
        if value is not None:
            check(
                field,
                getattr(
                    report.evidence_summary,
                    "conflict_count" if field == "conflicts" else "undetermined_count",
                ),
                value,
            )
    for fragment in gold.forbidden_output_fragments:
        check("source_prose_withheld:" + fragment, fragment in report.model_dump_json(), False)
    for attack in attacks:
        check("attack:" + attack["name"], attack["rejected"], True)
    failures = [c for c in checks if not c["passed"]]
    return {
        "case_id": case.case_id,
        "passed": not failures,
        "assertion_count": len(checks),
        "failures": failures[:100],
        "failure_count": len(failures),
        "failures_may_be_truncated": len(failures) > 100,
        "generated_claims": catalog.generated_count,
        "admitted_claims": len(catalog.claims),
        "validated_claims": len(validated),
        "validated_citations": sum(len(c.citations) for c in validated),
        "actual_graph_edges": len(rows),
        "expected_graph_edges": len(edges),
        "reviewed_claims_correct": required_correct,
        "reviewed_claims_total": len(gold.required_claims),
        "adversarial_rejected": sum(a["rejected"] for a in attacks),
        "adversarial_attempted": len(attacks),
        "source_truncated": gold.truncated,
        "abstention_required": gold.status == "ABSTAINED",
        "abstention_observed": report.explanation_status == "ABSTAINED",
        "deterministic_repeat": report.model_dump_json() == second.model_dump_json(),
        "required_warnings_present": sum(code in codes for code in gold.required_uncertainty_codes),
        "required_warnings_total": len(gold.required_uncertainty_codes),
        "noncausal_cases": int(
            report.causal_conclusion == "NOT_ESTABLISHED"
            and any(c.claim_type == "NO_CAUSAL_VERDICT" for c in report.claims)
        ),
    }


def run_explanation_suite(path):
    if version("relate-db") != "1.0.0":
        raise ToolError("UNSUPPORTED_ENGINE", "Explanation evaluation requires Relate 1.0.0.")
    raw = read_local_bytes(path)
    try:
        suite = ExplanationSuite.model_validate(parse_json_document(raw, max_depth=16))
    except ValidationError:
        raise ToolError(
            "INVALID_EXPLANATION_SUITE", "Explanation evaluation contract is invalid."
        ) from None
    if len({c.case_id for c in suite.cases}) != len(suite.cases):
        raise ToolError("INVALID_EXPLANATION_SUITE", "Case IDs must be unique.")
    results = []
    for case in suite.cases:
        with tempfile.TemporaryDirectory(prefix="traceweaver-explanation-eval-") as temporary:
            from pathlib import Path

            results.append(_case(Path(temporary) / "case.rl", case))

    def total(field):
        return sum(result[field] for result in results)

    return {
        "evaluation_contract_version": "1.0",
        "suite_id": suite.suite_id,
        "relate_version": version("relate-db"),
        "suite_sha256": hashlib.sha256(raw).hexdigest(),
        "synthetic_only": True,
        "scenarios_executed": len(results),
        "passed": sum(r["passed"] for r in results),
        "failed": sum(not r["passed"] for r in results),
        "cases": results,
        "metrics": {
            field: total(field)
            for field in (
                "generated_claims",
                "admitted_claims",
                "validated_claims",
                "validated_citations",
                "actual_graph_edges",
                "expected_graph_edges",
                "reviewed_claims_correct",
                "reviewed_claims_total",
                "adversarial_rejected",
                "adversarial_attempted",
                "abstention_required",
                "abstention_observed",
                "deterministic_repeat",
                "required_warnings_present",
                "required_warnings_total",
                "noncausal_cases",
            )
        },
        "whole_graph_completeness": None,
        "truncated_cases_excluded_from_completeness": [
            r["case_id"] for r in results if r["source_truncated"]
        ],
        "scope": "Returned admitted claims/citations only; no whole-graph accuracy metric.",
        "model_transport_runtime": "NOT_RUN_BY_OFFLINE_SUITE; separate controlled transport tests",
        "live_model_runtime": "NOT_RUN_BY_OFFLINE_SUITE",
        "causal_conclusion": "NOT_ESTABLISHED",
        "external_verification_status": "NOT_PERFORMED",
        "interpretation": (
            "Synthetic semantic/citation regression agreement, "
            "not source truth or root-cause accuracy."
        ),
    }


def evaluate_explanations(suite, output, *, overwrite=False):
    source, target = local_path(suite, must_exist=True), local_path(output)
    markdown = target.with_suffix(".md")
    if target.suffix != ".json":
        raise ToolError("INVALID_REPORT_PATH", "Select a separate .json output.")
    for path in (target, markdown):
        local_path(path)
        if path == source or (path.exists() and path.samefile(source)):
            raise ToolError("INVALID_REPORT_PATH", "Report cannot alias its input suite.")
        if path.exists() and not overwrite:
            raise ToolError("REPORT_EXISTS", "Existing reports require explicit --overwrite.")
    result = run_explanation_suite(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TraceWeaver synthetic explanation evaluation",
        "",
        f"Cases: {result['scenarios_executed']}; passed: {result['passed']}; "
        f"failed: {result['failed']}.",
        "",
        "Causation NOT_ESTABLISHED; external verification NOT_PERFORMED.",
        "",
        "Model transports and live inference are verified separately, not by this offline suite.",
        "",
        "| Case | Result | Assertions |",
        "| --- | --- | ---: |",
    ]
    lines += [
        f"| {c['case_id']} | {'PASS' if c['passed'] else 'FAIL'} | {c['assertion_count']} |"
        for c in result["cases"]
    ]
    lines += [
        "",
        "Metrics count returned admitted claims/citations, not whole-graph completeness.",
        "Truncated cases excluded from completeness: "
        + ", ".join(result["truncated_cases_excluded_from_completeness"]),
        "",
        "```json",
        canonical_json(result["metrics"]).rstrip(),
        "```",
        "",
    ]
    for path, text in [(target, canonical_json(result)), (markdown, "\n".join(lines))]:
        with path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    return result
