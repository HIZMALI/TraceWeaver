"""Strict explanation 1.0 contracts; no changes to the Investigation response."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from traceweaver.investigation_models import TemporalClass

ClaimType = Literal[
    "INCIDENT_OBSERVED",
    "SERVICE_AFFECTED",
    "DEPLOYMENT_CONNECTED",
    "DEPLOYMENT_BEFORE_ONSET",
    "DEPLOYMENT_NOT_PRECEDING",
    "EVIDENCE_REPORTED",
    "STRUCTURED_CONFLICT",
    "COMPARISON_UNDETERMINED",
    "SOURCE_UNVERIFIED",
    "CONTEXT_GAP",
    "NO_CAUSAL_VERDICT",
]
Identity = Annotated[str, Field(min_length=1, max_length=128)]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
ClaimId = Annotated[str, Field(pattern=r"^C-[a-f0-9]{24}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class ProofEdge(StrictModel):
    type: Literal[
        "AFFECTS",
        "DEPENDS_ON",
        "TARGETS",
        "INCLUDES_CHANGE",
        "HAS_EVIDENCE",
        "OBSERVED_ON",
        "RAISED_FOR",
    ]
    source_id: Identity
    target_id: Identity
    traversal_direction: Literal["FORWARD", "REVERSE"]


class ProofPath(StrictModel):
    node_ids: Annotated[list[Identity], Field(min_length=2, max_length=7)]
    edges: Annotated[list[ProofEdge], Field(min_length=1, max_length=6)]


class Citation(StrictModel):
    kind: Literal[
        "EVIDENCE", "GRAPH_PATH", "TEMPORAL", "CONTRADICTION", "GAP", "PROVENANCE", "INCIDENT"
    ]
    entity_ids: Annotated[list[Identity], Field(min_length=1, max_length=12)]
    graph_path: ProofPath | None = None
    event_utc: Annotated[str, Field(max_length=40)] | None = None
    temporal_classification: TemporalClass | None = None
    provenance_status: Literal["TRACEABLE", "INCOMPLETE", "INVALID"] | None = None
    verification_status: Literal["SYNTHETIC", "UNVERIFIED_EXTERNAL", "NOT_AVAILABLE"] | None = None
    source_ref: None = None
    source_ref_withheld: bool = False
    classification: Literal["CONFLICTING_OBSERVATIONS", "UNDETERMINED"] | None = None
    overlap_start: Annotated[str, Field(max_length=40)] | None = None
    overlap_end: Annotated[str, Field(max_length=40)] | None = None
    code: Annotated[str, Field(pattern=r"^[A-Z_]{1,64}$")] | None = None
    count: Annotated[int, Field(ge=0)] | None = None


class Claim(StrictModel):
    claim_id: ClaimId
    claim_type: ClaimType
    statement: Annotated[str, Field(min_length=1, max_length=1024)]
    referenced_entity_ids: Annotated[list[Identity], Field(min_length=1, max_length=12)]
    citations: Annotated[list[Citation], Field(min_length=1, max_length=12)]
    support_status: Literal["SUPPORTED_BY_RETURNED_CONTEXT"] = "SUPPORTED_BY_RETURNED_CONTEXT"


class AdmissibleClaimCatalog(StrictModel):
    investigation_fingerprint: Digest
    incident_id: Identity
    claims: Annotated[list[Claim], Field(min_length=1, max_length=128)]
    generated_count: Annotated[int, Field(ge=1)]
    truncated: bool


class EvidenceSummary(StrictModel):
    scope: Literal["RETURNED_EVIDENCE"] = "RETURNED_EVIDENCE"
    returned_candidates: int = Field(ge=0)
    returned_evidence: int = Field(ge=0)
    traceable_count: int = Field(ge=0)
    incomplete_count: int = Field(ge=0)
    invalid_count: int = Field(ge=0)
    unverified_external_count: int = Field(ge=0)
    not_evaluable_count: int = Field(ge=0)
    conflict_count: int = Field(ge=0)
    undetermined_count: int = Field(ge=0)


class Uncertainty(StrictModel):
    code: Annotated[str, Field(pattern=r"^[A-Z_]{1,64}$")]
    entity_ids: Annotated[list[Identity], Field(max_length=12)]
    count: int = Field(ge=0)
    references_omitted: bool


class ExplanationTruncation(StrictModel):
    investigation: dict[str, bool]
    catalog: bool
    selected_subset: bool
    uncertainties: bool
    next_checks: bool
    model_offer: bool = False


class ModelMetadata(StrictModel):
    provider: Literal["OLLAMA_LOCAL"] = "OLLAMA_LOCAL"
    model_id: Annotated[str, Field(min_length=1, max_length=128)]


class ExplanationReport(StrictModel):
    contract_version: Literal["1.0"] = "1.0"
    incident_id: Identity
    is_demo: bool | None
    mode_requested: Literal["DETERMINISTIC", "OLLAMA"]
    mode_executed: Literal["DETERMINISTIC", "OLLAMA", "NONE"]
    ai_generated_selection: bool
    model: ModelMetadata | None
    explanation_status: Literal[
        "EXPLAINED", "PARTIAL_CONTEXT", "ABSTAINED", "MODEL_UNAVAILABLE", "MODEL_OUTPUT_REJECTED"
    ]
    investigation_status: Literal["READY_FOR_REVIEW", "PARTIAL_CONTEXT", "INSUFFICIENT_EVIDENCE"]
    causal_conclusion: Literal["NOT_ESTABLISHED"] = "NOT_ESTABLISHED"
    investigation_fingerprint: Digest
    overview: Annotated[str, Field(max_length=2048)]
    claims: Annotated[list[Claim], Field(max_length=10)]
    evidence_summary: EvidenceSummary
    uncertainties: Annotated[list[Uncertainty], Field(max_length=20)]
    next_checks: Annotated[list[Annotated[str, Field(max_length=512)]], Field(max_length=8)]
    limitations: Annotated[list[Annotated[str, Field(max_length=512)]], Field(max_length=12)]
    truncation: ExplanationTruncation
    demo_notice: Annotated[str, Field(max_length=256)]
    catalog_claim_count: int = Field(ge=1, le=128)
    generated_claim_count: int = Field(ge=1)
    validated_claim_count: int = Field(ge=0, le=10)
    validated_citation_count: int = Field(ge=0, le=120)
    rejection_codes: Annotated[
        list[Annotated[str, Field(pattern=r"^[A-Z_]{1,64}$")]], Field(max_length=8)
    ] = Field(default_factory=list)
    external_verification_status: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"

    @model_validator(mode="after")
    def coherent_execution(self):
        if self.mode_executed == "OLLAMA":
            if (
                self.mode_requested != "OLLAMA"
                or not self.ai_generated_selection
                or self.model is None
            ):
                raise ValueError("Accepted local selection requires actual provider metadata")
        elif self.ai_generated_selection or self.model is not None:
            raise ValueError("No AI metadata without accepted provider execution")
        failed = self.explanation_status in {"MODEL_UNAVAILABLE", "MODEL_OUTPUT_REJECTED"}
        if failed != (self.mode_executed == "NONE") or (failed and self.claims):
            raise ValueError("Failed provider execution must not present accepted claims")
        if not failed and (not self.claims or self.claims[-1].claim_type != "NO_CAUSAL_VERDICT"):
            raise ValueError("Successful output must end with a causal caution")
        if self.validated_claim_count != len(self.claims) or self.validated_citation_count != sum(
            len(claim.citations) for claim in self.claims
        ):
            raise ValueError("Validation counts must describe the rendered claims")
        summary = self.evidence_summary
        if summary.returned_evidence != (
            summary.traceable_count + summary.incomplete_count + summary.invalid_count
        ):
            raise ValueError("Provenance categories must partition returned evidence")
        return self
