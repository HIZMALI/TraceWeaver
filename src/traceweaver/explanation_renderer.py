"""Controlled English templates. No model/source factual prose is rendered."""


def statement(kind: str, ids: list[str], citations: list) -> str:
    temporal = next((c for c in citations if c.kind == "TEMPORAL"), None)
    provenance = next((c for c in citations if c.kind == "PROVENANCE"), None)
    if kind == "INCIDENT_OBSERVED":
        return f"Incident {ids[0]} is in the returned graph context; onset is " + (
            f"{citations[0].event_utc}." if citations[0].event_utc else "unknown."
        )
    if kind == "SERVICE_AFFECTED":
        return f"Incident {ids[0]} has a returned AFFECTS link to service {ids[1]}."
    if kind == "DEPLOYMENT_CONNECTED":
        return (
            f"Deployment {ids[0]} is graph-connected to target {ids[1]}; connection is not cause."
        )
    if kind == "DEPLOYMENT_BEFORE_ONSET":
        return (
            f"Deployment {ids[0]} at {temporal.event_utc} is BEFORE onset within the requested "
            "window; temporal precedence does not establish causation."
        )
    if kind == "DEPLOYMENT_NOT_PRECEDING":
        return (
            f"Deployment {ids[0]} at {temporal.event_utc} is {temporal.temporal_classification}; "
            "it cannot be a preceding trigger and remains context."
        )
    if kind == "EVIDENCE_REPORTED":
        return (
            f"Evidence {ids[0]} belongs to this incident: {provenance.provenance_status} "
            f"metadata, {provenance.verification_status} source status. Source text is withheld."
        )
    if kind == "STRUCTURED_CONFLICT":
        return (
            f"Evidence {ids[0]} and {ids[1]} has comparable conflicting observations; "
            "reconcile them."
        )
    if kind == "COMPARISON_UNDETERMINED":
        return (
            f"Evidence {ids[0]} and {ids[1]} has an UNDETERMINED comparison; "
            "this is not a detected conflict."
        )
    if kind == "SOURCE_UNVERIFIED":
        return (
            f"Evidence {ids[0]} is UNVERIFIED_EXTERNAL; "
            "traceability does not authenticate its claims."
        )
    if kind == "CONTEXT_GAP":
        gap = citations[0]
        return f"Returned context reports {gap.code} (count {gap.count}); review the scoped gap."
    if kind == "NO_CAUSAL_VERDICT":
        return (
            "Causal conclusion is NOT_ESTABLISHED. "
            "Connected deployments are investigation candidates."
        )
    raise ValueError("Unknown controlled template")


def overview(status: str, ai: bool, summary) -> str:
    label = (
        "Local AI selected validated claim IDs." if ai else "Deterministic mode; not AI-generated."
    )
    if status in {"MODEL_UNAVAILABLE", "MODEL_OUTPUT_REJECTED"}:
        return (
            "Local model selection did not produce an accepted explanation. "
            "Cause is not established."
        )
    if status == "ABSTAINED":
        return (
            label + " Abstained from an incident explanation; review available scope and gaps. "
            "Cause is not established."
        )
    return (
        f"{label} Returned context contains {summary.returned_candidates} deployment/target pairs "
        f"and {summary.returned_evidence} evidence records. Structured audit: "
        f"{summary.conflict_count} conflicts and {summary.undetermined_count} undetermined pairs. "
        "This is scoped review context; cause is not established."
    )
