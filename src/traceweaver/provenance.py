"""Metadata traceability checks; never an external source truth-verification service."""

import math

from traceweaver.investigation_models import (
    EvidenceContext,
    Finding,
    GraphEdge,
    GraphPath,
    InvestigationOptions,
    ProvenanceAudit,
    TimestampValue,
)
from traceweaver.temporal import classify_time, entity_timestamp


def graph_properties(properties: dict) -> dict:
    """Keep non-JSON engine types visibly typed and invalid, rather than coercing to strings."""

    def value(item):
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, float) and math.isfinite(item):
            return item
        if isinstance(item, (list, tuple)):
            return [value(child) for child in item]
        if isinstance(item, dict):
            return {key: value(child) for key, child in item.items()}
        return {"unsupported_type": type(item).__name__, "representation": str(item)}

    return {key: value(item) for key, item in properties.items()}


def evidence_context(
    incident_id: str,
    properties: dict,
    service_ids: list[str],
    anchor: TimestampValue,
    options: InvestigationOptions,
) -> EvidenceContext:
    evidence_id = properties["id"]
    warnings = []
    invalid = False
    for field in ("source", "source_ref"):
        value = properties.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            warnings.append(
                Finding(
                    code=f"MISSING_{field.upper()}",
                    message=f"Evidence {field} is missing.",
                    entity_ids=[evidence_id],
                )
            )
        elif not isinstance(value, str):
            invalid = True
            warnings.append(
                Finding(
                    code=f"INVALID_{field.upper()}",
                    message=f"Evidence {field} must be a string.",
                    entity_ids=[evidence_id],
                )
            )
    timestamp = entity_timestamp(properties, "observed_at")
    if timestamp.warning_code:
        invalid |= timestamp.warning_code == "INVALID_TIMESTAMP"
        warnings.append(
            Finding(
                code=timestamp.warning_code,
                message="Evidence observation time is missing or invalid.",
                entity_ids=[evidence_id],
            )
        )
    base = GraphPath(
        node_ids=[incident_id, evidence_id],
        edges=[GraphEdge(type="HAS_EVIDENCE", source_id=incident_id, target_id=evidence_id)],
    )
    paths = [
        GraphPath(
            node_ids=base.node_ids + [service_id],
            edges=base.edges
            + [GraphEdge(type="OBSERVED_ON", source_id=evidence_id, target_id=service_id)],
        )
        for service_id in service_ids
    ]
    if not service_ids:
        paths = [base]
        warnings.append(
            Finding(
                code="MISSING_OBSERVED_SERVICE",
                message="No returned OBSERVED_ON service link grounds this evidence.",
                entity_ids=[evidence_id],
            )
        )
    demo = properties.get("demo")
    if type(demo) is not bool:
        warnings.append(
            Finding(
                code="UNKNOWN_DEMO_STATUS",
                message="Demo status is not a boolean.",
                entity_ids=[evidence_id],
            )
        )
    ref = properties.get("source_ref")
    has_ref = isinstance(ref, str) and bool(ref.strip())
    verification = (
        ("SYNTHETIC" if demo is True else "UNVERIFIED_EXTERNAL") if has_ref else "NOT_AVAILABLE"
    )
    return EvidenceContext(
        evidence_id=evidence_id,
        source=properties.get("source"),
        source_ref=ref,
        evidence_observed_at=timestamp,
        observed_service_ids=service_ids,
        graph_paths=paths,
        is_demo=demo if type(demo) is bool else None,
        provenance_status="INVALID" if invalid else "INCOMPLETE" if warnings else "TRACEABLE",
        verification_status=verification,
        warnings=warnings,
        properties=properties,
        **classify_time(timestamp, anchor, options).model_dump(),
    )


def audit_provenance(evidence: list[EvidenceContext]) -> ProvenanceAudit:
    warnings = [warning for item in evidence for warning in item.warnings]
    references = {}
    for item in evidence:
        if isinstance(item.source_ref, str) and item.source_ref.strip():
            references.setdefault(item.source_ref, []).append(item.evidence_id)
    for ids in references.values():
        if len(ids) > 1:
            warnings.append(
                Finding(
                    code="DUPLICATE_SOURCE_REFERENCE",
                    message="A shared source reference alone does not imply a contradiction.",
                    entity_ids=ids,
                    count=len(ids),
                )
            )
    return ProvenanceAudit(
        total_evidence=len(evidence),
        traceable_count=sum(e.provenance_status == "TRACEABLE" for e in evidence),
        incomplete_count=sum(e.provenance_status == "INCOMPLETE" for e in evidence),
        invalid_count=sum(e.provenance_status == "INVALID" for e in evidence),
        unverified_external_count=sum(
            e.verification_status == "UNVERIFIED_EXTERNAL" for e in evidence
        ),
        warnings=warnings[:100],
        warnings_may_be_truncated=len(warnings) > 100,
    )
