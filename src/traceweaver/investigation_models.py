"""Sprint 01 contracts, separate from the unchanged strict legacy context models."""

from typing import Annotated, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, JsonValue

T = TypeVar("T")
BoundedList = Annotated[list[T], Field(max_length=100)]
TemporalClass = Literal["BEFORE", "AT_ONSET", "AFTER", "OUTSIDE_WINDOW", "UNKNOWN"]


class InvestigationOptions(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    pre_minutes: int = Field(default=120, ge=0, le=1440)
    post_minutes: int = Field(default=30, ge=0, le=1440)
    max_candidates: int = Field(default=100, ge=1, le=100)
    max_evidence: int = Field(default=100, ge=1, le=100)


class Finding(BaseModel):
    code: str
    message: str
    entity_ids: BoundedList[str] = Field(default_factory=list)
    count: int = 1


class TimestampValue(BaseModel):
    source_field: str
    original: JsonValue = None
    utc: str | None = None
    warning_code: str | None = None


class GraphEdge(BaseModel):
    type: str
    source_id: str
    target_id: str
    traversal_direction: Literal["FORWARD", "REVERSE"] = "FORWARD"


class GraphPath(BaseModel):
    node_ids: Annotated[list[str], Field(max_length=7)]
    edges: Annotated[list[GraphEdge], Field(max_length=6)]


class TemporalAssessment(BaseModel):
    temporal_classification: TemporalClass
    temporal_reason: str


class ChangeContext(BaseModel):
    change_id: str
    properties: dict[str, JsonValue]
    graph_path: GraphPath


class Candidate(TemporalAssessment):
    deployment_id: str
    target_service_id: str
    change_ids: BoundedList[str]
    changes: BoundedList[ChangeContext]
    dependency_depth: int
    deployment_occurred_at: TimestampValue
    candidate_assessment: Literal["INVESTIGATE", "INSUFFICIENT_DATA", "TEMPORALLY_EXCLUDED"]
    assessment_reason: str
    graph_paths: BoundedList[GraphPath]
    properties: dict[str, JsonValue]


class EvidenceContext(TemporalAssessment):
    evidence_id: str
    source: JsonValue = None
    source_ref: JsonValue = None
    evidence_observed_at: TimestampValue
    observed_service_ids: BoundedList[str]
    graph_paths: BoundedList[GraphPath]
    is_demo: bool | None
    provenance_status: Literal["TRACEABLE", "INCOMPLETE", "INVALID"]
    verification_status: Literal["SYNTHETIC", "UNVERIFIED_EXTERNAL", "NOT_AVAILABLE"]
    warnings: BoundedList[Finding]
    properties: dict[str, JsonValue]


class ProvenanceAudit(BaseModel):
    scope: Literal["RETURNED_EVIDENCE"] = "RETURNED_EVIDENCE"
    total_evidence: int
    traceable_count: int
    incomplete_count: int
    invalid_count: int
    unverified_external_count: int
    warnings: BoundedList[Finding]
    warnings_may_be_truncated: bool = False


class Contradiction(BaseModel):
    evidence_ids: Annotated[list[str], Field(min_length=2, max_length=2)]
    signal_key: str
    service_id: str
    environment: str
    overlap_window: dict[str, str]
    observed_states: Annotated[list[str], Field(min_length=2, max_length=2)]
    reason: str
    classification: Literal["CONFLICTING_OBSERVATIONS", "UNDETERMINED"]


class ContradictionAudit(BaseModel):
    evaluable_evidence_count: int
    not_evaluable_count: int
    comparable_pair_count: int
    conflict_count: int
    undetermined_count: int
    warnings: BoundedList[Finding]


class TimelineEvent(TemporalAssessment):
    kind: Literal["INCIDENT", "DEPLOYMENT", "EVIDENCE"]
    entity_id: str
    target_service_id: str | None = None
    timestamp: TimestampValue


class DataQuality(BaseModel):
    status: Literal["COMPLETE", "INCOMPLETE", "INVALID"]
    unknown_timestamp_count: int
    provenance_issue_count: int
    structured_evidence_not_evaluable_count: int


class Investigation(BaseModel):
    incident_id: str
    is_demo: bool | None
    incident: dict[str, JsonValue]
    incident_started_at: str | None
    incident_time: TimestampValue
    window: dict[str, int]
    limits: dict[str, int]
    affected_services: BoundedList[dict[str, JsonValue]]
    candidates: BoundedList[Candidate]
    evidence: BoundedList[EvidenceContext]
    provenance_audit: ProvenanceAudit
    contradictions: BoundedList[Contradiction]
    contradiction_audit: ContradictionAudit
    timeline: BoundedList[TimelineEvent]
    data_quality: DataQuality
    investigation_status: Literal["READY_FOR_REVIEW", "PARTIAL_CONTEXT", "INSUFFICIENT_EVIDENCE"]
    status_reasons: BoundedList[str]
    causal_conclusion: Literal["NOT_ESTABLISHED"] = "NOT_ESTABLISHED"
    limitations: BoundedList[Finding]
    evidence_gaps: BoundedList[Finding]
    next_checks: BoundedList[str]
    truncation: dict[str, bool]
    results_may_be_truncated: bool
    interpretation: str = (
        "Deterministic graph context only. BEFORE means temporal suitability, not causation. "
        "TRACEABLE means metadata can be traced, not that an external source was verified."
    )
    demo_notice: str
