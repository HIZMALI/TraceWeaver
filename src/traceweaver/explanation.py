"""Shared graph-backed explanations; local model calls occur only after store closure."""

import re

from traceweaver.citation_validator import CitationRejected, CitationValidator
from traceweaver.explanation_catalog import build_catalog, select_deterministically
from traceweaver.explanation_models import (
    EvidenceSummary,
    ExplanationReport,
    ExplanationTruncation,
    ModelMetadata,
    Uncertainty,
)
from traceweaver.explanation_renderer import overview
from traceweaver.investigation import investigate
from traceweaver.investigation_models import Investigation, InvestigationOptions
from traceweaver.model_selection import accept_proposal
from traceweaver.ollama_local import OllamaFailure, OllamaLocal
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError


def summary_from(investigation):
    p, c = investigation.provenance_audit, investigation.contradiction_audit
    return EvidenceSummary(
        returned_candidates=len(investigation.candidates),
        returned_evidence=len(investigation.evidence),
        traceable_count=p.traceable_count,
        incomplete_count=p.incomplete_count,
        invalid_count=p.invalid_count,
        unverified_external_count=p.unverified_external_count,
        not_evaluable_count=c.not_evaluable_count,
        conflict_count=c.conflict_count,
        undetermined_count=c.undetermined_count,
    )


def explain_investigation(investigation, *, mode="deterministic", model=None):
    if mode not in {"deterministic", "ollama"}:
        raise ToolError("INVALID_EXPLANATION_MODE", "Select deterministic or ollama mode.")
    # Isolate from nested mutable input models before catalog/firewall/provider interaction.
    i = Investigation.model_validate_json(investigation.model_dump_json())
    catalog = build_catalog(i)
    summary = summary_from(i)
    failure = None
    offer_truncated = False
    executed, ai, metadata, abstain = "DETERMINISTIC", False, None, not i.evidence
    if mode == "ollama":
        try:
            raw, offered = OllamaLocal().select(catalog, model)
            offer_truncated = len(offered) < len(catalog.claims)
            claims, provider_abstain = accept_proposal(raw, i, catalog, offered)
            executed, ai, metadata = "OLLAMA", True, ModelMetadata(model_id=model)
            abstain |= provider_abstain
        except (OllamaFailure, CitationRejected) as exc:
            failure = exc
            executed, ai, metadata, claims = "NONE", False, None, []
    else:
        claims = CitationValidator(i, catalog).validate(
            select_deterministically(catalog), catalog.investigation_fingerprint
        )
    status = (
        "MODEL_UNAVAILABLE"
        if isinstance(failure, OllamaFailure) and failure.unavailable
        else "MODEL_OUTPUT_REJECTED"
        if failure
        else "ABSTAINED"
        if abstain
        else "EXPLAINED"
        if i.investigation_status == "READY_FOR_REVIEW"
        else "PARTIAL_CONTEXT"
    )
    findings = {g.code: g for g in i.evidence_gaps + i.limitations}
    for evidence in i.evidence:
        for warning in evidence.warnings:
            findings.setdefault(warning.code, warning)
    uncertainties = [
        Uncertainty(
            code=g.code,
            entity_ids=g.entity_ids[:12],
            count=g.count,
            references_omitted=len(g.entity_ids) > 12,
        )
        for g in sorted(findings.values(), key=lambda g: g.code)
    ]
    # These strings originate in Investigation, never in source prose/model output.
    next_checks = [
        s
        for s in i.next_checks
        if len(s) <= 512
        and not re.search(r"[\x00-\x1f]|://|[A-Za-z]:[\\/]|sk-|ghp_|password\s*[:=]", s, re.I)
    ]
    limitations = [
        "Cause is NOT_ESTABLISHED; graph connectivity and time order do not establish causation.",
        "External source truth verification is NOT_PERFORMED; TRACEABLE is not authenticated.",
        "Source prose and source references are withheld; stable graph IDs carry citation proof.",
        "Only returned context is explained; alternate paths and omitted data may matter.",
        "Row and output caps do not bound whole-store RAM or graph query cost.",
        "Model selects IDs only; deterministic templates render factual statements.",
    ]
    if i.results_may_be_truncated:
        limitations.append("Investigation is truncated; no completeness claim is justified.")
    if mode == "deterministic":
        limitations.append("Deterministic mode is not AI-generated and makes no model call.")
    if failure:
        limitations.append(
            "No accepted model selection; no automatic deterministic fallback was performed."
        )
        if isinstance(failure, OllamaFailure) and failure.unavailable:
            limitations.append(
                "Start local Ollama and supply --model with an already installed local model ID; "
                "this command never downloads models."
            )
    return ExplanationReport(
        incident_id=i.incident_id,
        is_demo=i.is_demo,
        mode_requested=mode.upper(),
        mode_executed=executed,
        ai_generated_selection=ai,
        model=metadata,
        explanation_status=status,
        investigation_status=i.investigation_status,
        investigation_fingerprint=catalog.investigation_fingerprint,
        overview=overview(status, ai, summary),
        claims=claims,
        evidence_summary=summary,
        uncertainties=uncertainties[:20],
        next_checks=next_checks[:8],
        limitations=limitations,
        truncation=ExplanationTruncation(
            investigation=i.truncation,
            catalog=catalog.truncated,
            selected_subset=len(claims) < len(catalog.claims),
            uncertainties=len(uncertainties) > 20,
            next_checks=len(next_checks) > 8 or len(next_checks) < len(i.next_checks),
            model_offer=offer_truncated,
        ),
        demo_notice=i.demo_notice,
        catalog_claim_count=len(catalog.claims),
        generated_claim_count=catalog.generated_count,
        validated_claim_count=len(claims),
        validated_citation_count=sum(len(c.citations) for c in claims),
        rejection_codes=[failure.code] if failure else [],
    )


def explain(
    database,
    incident_id: str,
    options: InvestigationOptions | None = None,
    *,
    mode="deterministic",
    model=None,
) -> ExplanationReport:
    with GraphStore(database) as store:
        investigation = investigate(store, incident_id, options)
    return explain_investigation(investigation, mode=mode, model=model)
