"""Finite model-directed native graph research with existing semantic claim admission."""

import time

from pydantic import ValidationError

from traceweaver.agent_models import (
    AgentInvestigationReport,
    ToolArguments,
    canonical_agent_digest,
)
from traceweaver.agent_provider import (
    TOTAL_SECONDS,
    AgentFinalProposal,
    AgentProvider,
    tool_definitions,
)
from traceweaver.agent_tools import HANDLERS, create_context, execute_tool
from traceweaver.citation_validator import CitationRejected
from traceweaver.local_files import canonical_json, parse_json_document
from traceweaver.model_selection import accept_proposal, sanitized_packet
from traceweaver.ollama_local import OllamaFailure
from traceweaver.tool_errors import ToolError


def _edge_keys(paths):
    return {(e.type, e.source_id, e.target_id) for p in paths for e in p.edges}


def retrieved_claims(context, steps):
    """A source-admissible claim also needs support actually returned by executed native tools."""
    edges = _edge_keys([p for s in steps for p in s.result.graph_paths])
    records = [r for s in steps for r in s.result.records]
    pairs = [p for s in steps for p in s.result.comparisons]
    gaps = {code for s in steps if s.tool_name == "inspect_gaps" for code in s.result.gap_codes}

    def supported(c):
        if not steps:
            return False
        for x in c.citations:
            if x.kind == "GRAPH_PATH" and not _edge_keys([x.graph_path]).issubset(edges):
                return False
            if x.kind in {"EVIDENCE", "PROVENANCE"}:
                matched = [
                    r
                    for r in records
                    if r.entity_id == x.entity_ids[0] and r.provenance_status is not None
                ]
                if not matched:
                    return False
                if x.kind == "PROVENANCE" and not any(
                    r.provenance_status == x.provenance_status
                    and r.verification_status == x.verification_status
                    for r in matched
                ):
                    return False
            if x.kind in {"TEMPORAL", "INCIDENT"}:
                if not any(
                    r.entity_id == x.entity_ids[0]
                    and r.timestamp.utc == x.event_utc
                    and (
                        x.kind == "INCIDENT"
                        or r.temporal_classification == x.temporal_classification
                    )
                    for r in records
                ):
                    return False
            if x.kind == "CONTRADICTION" and not any(
                p.evidence_ids == x.entity_ids[:2]
                and p.service_id == x.entity_ids[2]
                and p.classification == x.classification
                and p.overlap_window["start"] == x.overlap_start
                and p.overlap_window["end"] == x.overlap_end
                for p in pairs
            ):
                return False
            if x.kind == "GAP" and x.code != "NO_CAUSAL_VERDICT" and x.code not in gaps:
                return False
        return True

    return [c for c in context.catalog.claims if supported(c)]


def opaque_result(context, step):
    def handle(identity):
        if identity not in context.node_handles:
            raise ToolError("AGENT_NODE_SCOPE", "Native identity is outside provider handle scope.")
        return context.node_handles[identity]

    return {
        "step_number": step.step_number,
        "status": step.result.status,
        "entity_handles": [handle(v) for v in step.result.entity_ids],
        "paths": [
            {
                "nodes": [handle(v) for v in p.node_ids],
                "edges": [
                    {
                        "type": e.type,
                        "source": handle(e.source_id),
                        "target": handle(e.target_id),
                        "traversal_direction": e.traversal_direction,
                    }
                    for e in p.edges
                ],
            }
            for p in step.result.graph_paths
        ],
        "records": [
            {
                "entity": handle(r.entity_id),
                "utc": r.timestamp.utc,
                "temporal_classification": r.temporal_classification,
                "provenance_status": r.provenance_status,
                "verification_status": r.verification_status,
            }
            for r in step.result.records
        ],
        "comparisons": [
            {
                "classification": p.classification,
                "service": handle(p.service_id),
                "evidence": [handle(v) for v in p.evidence_ids],
                "overlap_window": p.overlap_window,
            }
            for p in step.result.comparisons
        ],
        "gap_codes": step.result.gap_codes,
        "truncated": step.result.truncated,
    }


def make_report(
    context,
    intent,
    steps,
    claims,
    status,
    start,
    *,
    provider=None,
    codes=(),
    model_executed=None,
    warnings=(),
):
    data = dict(
        incident_id=context.source.incident_id,
        source_fingerprint=context.source_fingerprint,
        database_digest=context.database_digest,
        options=context.options,
        intent=intent,
        mode_executed="DETERMINISTIC_TOOL_REHEARSAL"
        if provider is None
        else "OLLAMA"
        if model_executed
        else "NONE",
        model_requested=None if provider is None else provider.model,
        model_executed=model_executed,
        agent_status=status,
        ai_directed_tools=any(s.selected_by == "LOCAL_MODEL" for s in steps),
        ai_generated_selection=bool(provider and steps and claims and status != "ABSTAINED"),
        tool_trace=steps,
        validated_claims=claims,
        validated_citation_count=sum(len(c.citations) for c in claims),
        rejection_codes=list(codes)[:8],
        proposal_warnings=list(warnings)[:4],
        gap_codes=sorted({g.code for g in context.source.evidence_gaps})[:20],
        source_truncated=context.source.results_may_be_truncated,
        model_subjects_truncated=context.subjects_truncated,
        model_interactions=0 if provider is None else provider.interactions,
        native_query_count=context.native_queries,
        elapsed_ms=round((time.monotonic() - start) * 1000, 3),
        synthetic_notice=context.source.demo_notice,
    )
    # Construct only to include explicit defaults for hashing; full validation occurs immediately.
    value = AgentInvestigationReport.model_construct(**data, canonical_fingerprint="0" * 64)
    data = {**value.model_dump(), "canonical_fingerprint": canonical_agent_digest(value)}
    report = AgentInvestigationReport.model_validate(data)
    if len(report.model_dump_json().encode()) > 524288:
        raise ToolError("AGENT_REPORT_LIMIT", "Agent report exceeds byte bound.")
    return report


def parse_tool(message, expected_index=0):
    calls = message.get("tool_calls")
    if not isinstance(calls, list) or len(calls) != 1:
        raise ToolError(
            "AGENT_MULTI_TOOL_REJECTED", "Exactly one native tool per round is allowed."
        )
    if message["content"].strip():
        raise ToolError(
            "AGENT_TOOL_PROSE_REJECTED", "Tool selection may not contain narrative output."
        )
    call = calls[0]
    if (
        not isinstance(call, dict)
        or set(call) - {"type", "id", "function"}
        or call.get("type", "function") != "function"
    ):
        raise ToolError("AGENT_CALL_SCHEMA", "Native tool-call schema is invalid.")
    function = call.get("function")
    if (
        not isinstance(function, dict)
        or set(function) - {"name", "arguments", "index"}
        or not isinstance(function.get("name"), str)
    ):
        raise ToolError("AGENT_CALL_SCHEMA", "Native function schema is invalid.")
    if "index" in function and (
        type(function["index"]) is not int or function["index"] != expected_index
    ):
        raise ToolError("AGENT_CALL_SCHEMA", "A single native call has index zero.")
    if "id" in call and (not isinstance(call["id"], str) or len(call["id"]) > 64):
        raise ToolError("AGENT_CALL_SCHEMA", "Native call ID exceeds its bound.")
    try:
        arguments = ToolArguments.model_validate(function.get("arguments"))
    except ValidationError:
        raise ToolError("AGENT_ARGUMENT_SCHEMA", "Tool arguments are invalid.") from None
    return function["name"], arguments


def constrain_proposals(context, message, used):
    """Validate the full batch; execute one. Bad IDs or functions are never repaired."""
    calls = message.get("tool_calls")
    if not isinstance(calls, list) or not 1 <= len(calls) <= 4:
        raise ToolError("AGENT_MULTI_TOOL_REJECTED", "Native proposal batch exceeds its bound.")
    parsed = []
    seen = set()
    for index, call in enumerate(calls):
        name, args = parse_tool({"content": message["content"], "tool_calls": [call]}, index)
        if name not in HANDLERS:
            raise ToolError("AGENT_TOOL_REJECTED", "Only fixed native tools are admitted.")
        subject = context.subjects.get(args.subject)
        if not subject or subject[0] != HANDLERS[name][0]:
            raise ToolError("AGENT_SUBJECT_REJECTED", "Proposal is outside offered native scope.")
        if (name, args.subject) in used or (name, args.subject) in seen:
            raise ToolError("AGENT_REPEATED_ACTION", "Repeated native proposal rejected.")
        seen.add((name, args.subject))
        parsed.append((name, args))
    return *parsed[0], len(parsed) - 1


def admit_finish(context, steps, content):
    if not isinstance(content, str) or len(content.encode()) > 4096:
        raise ToolError("AGENT_FINISH_LIMIT", "Final proposal exceeds byte bound.")
    try:
        proposal = AgentFinalProposal.model_validate(
            parse_json_document(content.encode(), max_depth=4)
        )
    except (ValidationError, ToolError):
        raise ToolError("AGENT_FINISH_SCHEMA", "Final proposal schema is invalid.") from None
    if proposal.investigation_fingerprint != context.source_fingerprint:
        raise ToolError("SNAPSHOT_MISMATCH", "Final source fingerprint is invalid.")
    if any(v not in [s.step_number for s in steps] for v in proposal.tool_steps) or len(
        proposal.tool_steps
    ) != len(set(proposal.tool_steps)):
        raise ToolError("AGENT_UNKNOWN_STEP", "Final proposal cites an unexecuted/duplicate step.")
    catalog_ids = {c.claim_id for c in context.catalog.claims}
    if set(proposal.selected_claim_ids) - catalog_ids:
        raise ToolError("UNKNOWN_CLAIM_ID", "Final proposal contains an unknown claim ID.")
    if not steps:
        return [], "MODEL_SELECTION_ONLY"
    offered = [c.claim_id for c in retrieved_claims(context, steps)]
    if set(proposal.selected_claim_ids) - set(offered):
        raise ToolError("CLAIM_NOT_RETRIEVED", "Claim support was not returned by executed tools.")
    raw = canonical_json(proposal.model_dump(exclude={"tool_steps"})).encode()
    claims, abstain = accept_proposal(raw, context.source, context.catalog, offered)
    status = (
        "ABSTAINED"
        if abstain or not context.source.evidence
        else "PARTIAL_CONTEXT"
        if context.source.investigation_status != "READY_FOR_REVIEW"
        else "COMPLETED"
    )
    return claims, status


def run_agent(database, action):
    start = time.monotonic()
    deadline = start + TOTAL_SECONDS
    context = create_context(
        database, action.incident_id, action.options, action.source_fingerprint
    )
    provider = AgentProvider(action.model_id, deadline)
    steps = []
    used = set()
    warnings = []
    executed = None
    system = (
        "Use one native graph tool per round, only offered opaque subjects. Never write facts, "
        "Cypher, URLs or narrative. Do not repeat calls. Review is not a causal verdict. "
        "After native retrieval, finish with JSON only: investigation_fingerprint, "
        "selected_claim_ids, "
        "focus (BALANCED/TIMELINE/DEPENDENCIES/EVIDENCE/GAPS), abstain, optional tool_steps. "
        "Select 3 to 8 retrieved_claims, fewer if fewer are available; or abstain with no IDs. "
        "No raw entity IDs/source prose are available. Tools establish neither cause nor truth."
        " Inspect a deployment or evidence after scope before finishing the requested review. "
        "For multiple proposals the whole batch is validated but only its FIRST call is executed. "
        "Other proposed calls are NOT executed. Prefer exactly one call per round."
    )
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": canonical_json(
                {
                    "intent": action.intent,
                    "investigation_fingerprint": context.source_fingerprint,
                    "subjects": [
                        {"subject": key, "kind": kind}
                        for key, (kind, _) in context.subjects.items()
                    ],
                    "retrieved_claims": [],
                    "source_truncated": context.source.results_may_be_truncated,
                }
            ),
        },
    ]
    try:
        if time.monotonic() >= deadline:
            raise ToolError("AGENT_TIME_BUDGET", "Agent deadline exhausted before provider check.")
        provider.check_installed()
        for n in range(5):
            if time.monotonic() >= deadline:
                raise ToolError("AGENT_TIME_BUDGET", "Agent deadline exhausted.")
            context.guard()
            tools = tool_definitions(context, used) if len(steps) < 4 else []
            message = provider.chat(messages, tools, final=n == 4 or not tools)
            executed = action.model_id
            context.guard()
            if message.get("tool_calls"):
                if len(steps) >= 4:
                    raise ToolError("AGENT_TOOL_BUDGET", "Native call budget exhausted.")
                name, args, deferred = constrain_proposals(context, message, used)
                if (name, args.subject) in used:
                    raise ToolError("AGENT_REPEATED_ACTION", "Repeated native action rejected.")
                step = execute_tool(
                    context,
                    name,
                    args.model_dump(),
                    step_number=len(steps) + 1,
                    selected_by="LOCAL_MODEL",
                )
                if deferred:
                    step = step.model_copy(update={"deferred_proposal_count": deferred})
                    if "PARALLEL_PROPOSALS_CONSTRAINED" not in warnings:
                        warnings.append("PARALLEL_PROPOSALS_CONSTRAINED")
                steps.append(step)
                used.add((name, args.subject))
                metadata = {c["claim_id"]: c for c in sanitized_packet(context.catalog)["claims"]}
                available = [
                    metadata[c.claim_id]
                    for c in retrieved_claims(context, steps)
                    if c.claim_id in metadata
                ]
                messages += [
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {"function": {"name": name, "arguments": args.model_dump()}}
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_name": name,
                        "content": canonical_json(
                            {
                                "result": opaque_result(context, step),
                                "retrieved_claims": available,
                                "remaining_tool_calls": 4 - len(steps),
                                "unexecuted_parallel_proposals": deferred,
                                "investigation_fingerprint": context.source_fingerprint,
                            }
                        ),
                    },
                ]
            else:
                if steps and n < 4:
                    # Native chat normally ends tool selection with prose. It is not a claim
                    # proposal: discard it, never echo it, and enter the declared final-ID phase.
                    if message["content"].strip() and "READ_PHASE_TEXT_NOT_USED" not in warnings:
                        warnings.append("READ_PHASE_TEXT_NOT_USED")
                    metadata = {
                        c["claim_id"]: c for c in sanitized_packet(context.catalog)["claims"]
                    }
                    final_packet = {
                        "task": "FINAL_CLAIM_IDS_ONLY",
                        "investigation_fingerprint": context.source_fingerprint,
                        "retrieved_claims": [
                            metadata[c.claim_id]
                            for c in retrieved_claims(context, steps)
                            if c.claim_id in metadata
                        ],
                        "executed_steps": [s.step_number for s in steps],
                    }
                    context.guard()
                    message = provider.chat(
                        messages + [{"role": "user", "content": canonical_json(final_packet)}],
                        [],
                        final=True,
                    )
                    context.guard()
                    if message.get("tool_calls"):
                        raise ToolError(
                            "AGENT_FINAL_TOOL_REJECTED", "Final phase cannot execute tools."
                        )
                claims, status = admit_finish(context, steps, message["content"])
                context.guard()
                return make_report(
                    context,
                    action.intent,
                    steps,
                    claims,
                    status,
                    start,
                    provider=provider,
                    model_executed=executed,
                    warnings=warnings,
                )
        raise ToolError("AGENT_MODEL_BUDGET", "Model interaction budget exhausted.")
    except (ToolError, CitationRejected) as exc:
        code = exc.code
        status = (
            "STALE_SNAPSHOT"
            if code in {"STALE_SNAPSHOT", "SNAPSHOT_MISMATCH"}
            else "BUDGET_EXHAUSTED"
            if code
            in {
                "AGENT_TIME_BUDGET",
                "AGENT_MODEL_BUDGET",
                "AGENT_TOOL_BUDGET",
                "AGENT_QUERY_BUDGET",
            }
            else "MODEL_UNAVAILABLE"
            if isinstance(exc, OllamaFailure) and exc.unavailable
            else "MODEL_OUTPUT_REJECTED"
        )
        return make_report(
            context,
            action.intent,
            steps,
            [],
            status,
            start,
            provider=provider,
            codes=[code],
            model_executed=executed,
            warnings=warnings,
        )
