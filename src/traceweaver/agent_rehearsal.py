"""Offline fixed plans over the same native tools; never presented as AI activity."""

import time

from traceweaver.agent import make_report, retrieved_claims
from traceweaver.agent_tools import create_context, execute_tool
from traceweaver.citation_validator import CitationValidator
from traceweaver.explanation_catalog import select_deterministically
from traceweaver.tool_errors import ToolError


def fixed_plan(context, intent):
    plan = [("get_incident_scope", "I000")]
    deployments = [k for k, (kind, _) in context.subjects.items() if kind == "deployment"]
    evidence = [k for k, (kind, _) in context.subjects.items() if kind == "evidence"]
    pairs = [k for k, (kind, _) in context.subjects.items() if kind == "comparison"]
    if intent == "CHECK_COMPETING_DEPLOYMENTS":
        plan += [("trace_deployment", k) for k in deployments[:2]]
    elif intent == "TRACE_DEPENDENCY_PATH":
        if deployments:
            deepest = max(
                deployments,
                key=lambda k: next(
                    c.dependency_depth
                    for c in context.source.candidates
                    if (c.deployment_id, c.target_service_id) == context.subjects[k][1]
                ),
            )
            plan.append(("trace_deployment", deepest))
        plan += [("inspect_evidence", k) for k in evidence[:1]]
    elif intent == "RECONCILE_OBSERVATIONS":
        pairs.sort(
            key=lambda k: next(
                p.classification != "CONFLICTING_OBSERVATIONS"
                for p in context.source.contradictions
                if tuple(p.evidence_ids) == context.subjects[k][1]
            )
        )
        plan += [("compare_observations", k) for k in pairs[:2]]
        if not pairs:
            plan += [("inspect_evidence", k) for k in evidence[:2]]
    elif intent == "FIND_EVIDENCE_GAPS":
        evidence.sort(
            key=lambda k: next(
                e.provenance_status == "TRACEABLE"
                for e in context.source.evidence
                if (e.evidence_id,) == context.subjects[k][1]
            )
        )
        plan += [("inspect_evidence", k) for k in evidence[:2]]
    else:
        raise ToolError("AGENT_INTENT_REJECTED", "Unknown fixed plan.")
    return plan[:3] + [("inspect_gaps", "I000")]


def run_rehearsal(database, action):
    start = time.monotonic()
    context = create_context(
        database, action.incident_id, action.options, action.source_fingerprint
    )
    steps = []
    try:
        for name, subject in fixed_plan(context, action.intent):
            if time.monotonic() - start >= 30:
                raise ToolError("AGENT_TIME_BUDGET", "Offline tool deadline exhausted.")
            steps.append(
                execute_tool(
                    context,
                    name,
                    {"subject": subject},
                    step_number=len(steps) + 1,
                    selected_by="DETERMINISTIC_PLAN",
                )
            )
        supported = retrieved_claims(context, steps)
        subset = context.catalog.model_copy(update={"claims": supported})
        claims = CitationValidator(context.source, context.catalog).validate(
            select_deterministically(subset), context.source_fingerprint
        )
        context.guard()
        status = (
            "ABSTAINED"
            if not context.source.evidence
            else "PARTIAL_CONTEXT"
            if context.source.investigation_status != "READY_FOR_REVIEW"
            else "COMPLETED"
        )
        return make_report(context, action.intent, steps, claims, status, start)
    except ToolError as exc:
        status = "STALE_SNAPSHOT" if exc.code == "STALE_SNAPSHOT" else "BUDGET_EXHAUSTED"
        return make_report(context, action.intent, steps, [], status, start, codes=[exc.code])
