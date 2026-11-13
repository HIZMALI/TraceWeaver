"""Strict privacy-conscious console projection, separate from every legacy response."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from traceweaver.explanation_models import (
    Digest,
    ExplanationReport,
    Identity,
    ProofPath,
    StrictModel,
)
from traceweaver.investigation_models import InvestigationOptions, TemporalClass


class DisplayTime(StrictModel):
    utc: str | None
    original: Annotated[str, Field(max_length=96)] | None
    warning_code: str | None
    original_withheld: bool


class DisplayLabel(StrictModel):
    text: Annotated[str, Field(max_length=160)]
    status: Literal["RETURNED_TEXT", "WITHHELD", "SHORTENED"]


class ConsoleIncident(StrictModel):
    id: Identity
    title: Annotated[str, Field(max_length=160)]
    severity: Annotated[str, Field(max_length=160)]
    status: Annotated[str, Field(max_length=160)]
    metadata_withheld: bool


class ConsoleIncidents(StrictModel):
    contract_version: Literal["1.0"] = "1.0"
    incidents: Annotated[list[ConsoleIncident], Field(max_length=100)]
    results_may_be_truncated: bool
    unsafe_identifiers_omitted: int = Field(ge=0, le=100)


class ViewFinding(StrictModel):
    code: str
    count: int
    entity_ids: Annotated[list[Identity], Field(max_length=20)]
    references_omitted: bool


class ViewService(StrictModel):
    id: Identity
    name: DisplayLabel


class ViewChange(StrictModel):
    change_id: Identity
    name: DisplayLabel
    graph_path: ProofPath


class ViewCandidate(StrictModel):
    deployment_id: Identity
    target_service_id: Identity
    name: DisplayLabel
    dependency_depth: int
    temporal_classification: TemporalClass
    candidate_assessment: Literal["INVESTIGATE", "INSUFFICIENT_DATA", "TEMPORALLY_EXCLUDED"]
    deployment_occurred_at: DisplayTime
    graph_paths: Annotated[list[ProofPath], Field(max_length=100)]
    changes: Annotated[list[ViewChange], Field(max_length=100)]


class ViewEvidence(StrictModel):
    evidence_id: Identity
    is_demo: bool | None
    evidence_observed_at: DisplayTime
    temporal_classification: TemporalClass
    observed_service_ids: Annotated[list[Identity], Field(max_length=100)]
    graph_paths: Annotated[list[ProofPath], Field(max_length=100)]
    provenance_status: Literal["TRACEABLE", "INCOMPLETE", "INVALID"]
    verification_status: Literal["SYNTHETIC", "UNVERIFIED_EXTERNAL", "NOT_AVAILABLE"]
    warnings: Annotated[list[ViewFinding], Field(max_length=100)]
    source_reference: Literal["WITHHELD", "NOT_AVAILABLE"]


class ViewComparison(StrictModel):
    evidence_ids: Annotated[list[Identity], Field(min_length=2, max_length=2)]
    service_id: Identity
    signal_key: DisplayLabel
    environment: DisplayLabel
    overlap_window: dict[str, str]
    observed_states: Annotated[
        list[Literal["HEALTHY", "FAILED", "DEGRADED"]], Field(min_length=2, max_length=2)
    ]
    classification: Literal["CONFLICTING_OBSERVATIONS", "UNDETERMINED"]


class ViewEvent(StrictModel):
    kind: Literal["INCIDENT", "DEPLOYMENT", "EVIDENCE"]
    entity_id: Identity
    target_service_id: Identity | None
    timestamp: DisplayTime
    temporal_classification: TemporalClass


class DashboardInvestigation(StrictModel):
    incident_id: Identity
    is_demo: bool | None
    title: DisplayLabel
    severity: DisplayLabel
    status: DisplayLabel
    incident_time: DisplayTime
    options: InvestigationOptions
    investigation_status: Literal["READY_FOR_REVIEW", "PARTIAL_CONTEXT", "INSUFFICIENT_EVIDENCE"]
    causal_conclusion: Literal["NOT_ESTABLISHED"]
    entity_kinds: Annotated[
        dict[Identity, Literal["Incident", "Service", "Deployment", "Change", "Evidence"]],
        Field(max_length=1000),
    ]
    affected_services: Annotated[list[ViewService], Field(max_length=100)]
    candidates: Annotated[list[ViewCandidate], Field(max_length=100)]
    evidence: Annotated[list[ViewEvidence], Field(max_length=100)]
    contradictions: Annotated[list[ViewComparison], Field(max_length=100)]
    timeline: Annotated[list[ViewEvent], Field(max_length=100)]
    evidence_gaps: Annotated[list[ViewFinding], Field(max_length=100)]
    truncation: dict[str, bool]
    results_may_be_truncated: bool


class DashboardBundle(StrictModel):
    contract_version: Literal["1.0"] = "1.0"
    source_fingerprint: Digest
    view_fingerprint: Digest
    read_only: Literal[True] = True
    investigation: DashboardInvestigation
    explanation: ExplanationReport

    @model_validator(mode="after")
    def coherent(self):
        from traceweaver.dashboard import view_digest

        if (
            self.source_fingerprint != self.explanation.investigation_fingerprint
            or self.investigation.incident_id != self.explanation.incident_id
            or self.investigation.is_demo != self.explanation.is_demo
            or len(self.investigation.evidence)
            != self.explanation.evidence_summary.returned_evidence
            or len(self.investigation.candidates)
            != self.explanation.evidence_summary.returned_candidates
            or self.view_fingerprint
            != view_digest(self.investigation, self.explanation, self.source_fingerprint)
        ):
            raise ValueError("Dashboard snapshot is incoherent")
        return self
