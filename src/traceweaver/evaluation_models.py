"""Frozen, independently authored gold labels for an offline synthetic evaluation."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from traceweaver.ingestion_models import ContractModel
from traceweaver.investigation_models import InvestigationOptions

TemporalLabel = Literal["BEFORE", "AT_ONSET", "AFTER", "OUTSIDE_WINDOW", "UNKNOWN"]
Identifier = Annotated[str, Field(min_length=1, max_length=128)]


class GoldEdge(ContractModel):
    type: Literal[
        "AFFECTS",
        "DEPENDS_ON",
        "TARGETS",
        "INCLUDES_CHANGE",
        "HAS_EVIDENCE",
        "OBSERVED_ON",
        "RAISED_FOR",
    ]
    source_id: Identifier
    target_id: Identifier
    traversal_direction: Literal["FORWARD", "REVERSE"]


class GoldPath(ContractModel):
    node_ids: Annotated[list[Identifier], Field(min_length=2, max_length=7)]
    edges: Annotated[list[GoldEdge], Field(min_length=1, max_length=6)]


class CandidateGold(ContractModel):
    deployment_id: Identifier
    target_service_id: Identifier
    dependency_depth: int = Field(ge=0, le=3)
    temporal_classification: TemporalLabel
    candidate_assessment: Literal["INVESTIGATE", "INSUFFICIENT_DATA", "TEMPORALLY_EXCLUDED"]
    event_utc: str | None
    change_ids: Annotated[list[Identifier], Field(max_length=100)]
    graph_path: GoldPath


class EvidenceGold(ContractModel):
    evidence_id: Identifier
    temporal_classification: TemporalLabel
    event_utc: str | None
    observed_service_ids: Annotated[list[Identifier], Field(max_length=100)]
    provenance_status: Literal["TRACEABLE", "INCOMPLETE", "INVALID"]
    verification_status: Literal["SYNTHETIC", "UNVERIFIED_EXTERNAL", "NOT_AVAILABLE"]
    warning_codes: Annotated[list[Identifier], Field(max_length=20)]


class GoldTruncation(ContractModel):
    candidates: bool
    evidence: bool
    affected_services: bool
    changes: bool
    observations: bool
    timeline: bool
    contradictions: bool
    provenance_warnings: bool


Pair = Annotated[list[Identifier], Field(min_length=2, max_length=2)]


class GoldExpectation(ContractModel):
    candidates: Annotated[list[CandidateGold], Field(max_length=100)]
    evidence: Annotated[list[EvidenceGold], Field(max_length=100)]
    conflict_pairs: Annotated[list[Pair], Field(max_length=100)]
    undetermined_pairs: Annotated[list[Pair], Field(max_length=100)]
    not_evaluable_count: int = Field(ge=0, le=100)
    investigation_status: Literal["READY_FOR_REVIEW", "PARTIAL_CONTEXT", "INSUFFICIENT_EVIDENCE"]
    causal_conclusion: Literal["NOT_ESTABLISHED"]
    truncation: GoldTruncation
    required_limitation_codes: Annotated[list[Identifier], Field(max_length=100)]

    @model_validator(mode="after")
    def distinct_labels(self):
        candidates = {(c.deployment_id, c.target_service_id) for c in self.candidates}
        evidence = {e.evidence_id for e in self.evidence}
        if len(candidates) != len(self.candidates) or len(evidence) != len(self.evidence):
            raise ValueError("Duplicate gold identity")
        for pairs in (self.conflict_pairs, self.undetermined_pairs):
            keys = {tuple(sorted(pair)) for pair in pairs}
            if len(keys) != len(pairs) or any(len(set(pair)) != 2 for pair in pairs):
                raise ValueError("Duplicate or invalid gold comparison pair")
        return self


class EvaluationCase(ContractModel):
    case_id: Identifier
    description: Annotated[str, Field(max_length=4096)]
    fixture_profiles: Annotated[
        list[Literal["baseline", "sprint01", "evaluation", "caps"]],
        Field(min_length=1, max_length=4),
    ]
    incident_id: Identifier
    options: InvestigationOptions
    expected: GoldExpectation

    @model_validator(mode="after")
    def unique_profiles(self):
        if len(set(self.fixture_profiles)) != len(self.fixture_profiles):
            raise ValueError("Duplicate fixture profile")
        return self


class EvaluationSuite(ContractModel):
    suite_version: Literal["1.0"]
    suite_id: Identifier
    gold_authoring: Annotated[str, Field(max_length=4096)]
    cases: Annotated[list[EvaluationCase], Field(min_length=1, max_length=64)]

    @model_validator(mode="after")
    def unique_cases(self):
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError("Duplicate case identity")
        return self
