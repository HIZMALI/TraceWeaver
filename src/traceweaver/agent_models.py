"""Agent 1.0 is separate from every existing investigation/explanation response."""

import hashlib
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from traceweaver.console_selection import SelectionRequest
from traceweaver.dashboard_models import DisplayTime, ViewComparison
from traceweaver.explanation_models import Claim, Digest, Identity, ProofPath, StrictModel
from traceweaver.investigation_models import InvestigationOptions, TemporalClass
from traceweaver.local_files import canonical_json

Intent = Literal[
    "CHECK_COMPETING_DEPLOYMENTS",
    "TRACE_DEPENDENCY_PATH",
    "RECONCILE_OBSERVATIONS",
    "FIND_EVIDENCE_GAPS",
]
ToolName = Literal[
    "get_incident_scope",
    "trace_deployment",
    "inspect_evidence",
    "compare_observations",
    "inspect_gaps",
]
OpaqueSubject = Annotated[str, Field(pattern=r"^[IDEP][0-9]{3}$")]
Code = Annotated[str, Field(pattern=r"^[A-Z_]{1,64}$")]
NO_CAUSE = (
    "Causal conclusion is NOT_ESTABLISHED. Connected deployments are investigation candidates."
)


class AgentScopeRequest(StrictModel):
    incident_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")]
    options: InvestigationOptions
    source_fingerprint: Digest
    intent: Intent
    confirmed: Literal[True]

    @field_validator("confirmed", mode="before")
    @classmethod
    def confirmation(cls, value):
        if value is not True:
            raise ValueError("Explicit confirmation required")
        return value


class AgentRequest(AgentScopeRequest):
    model_id: Annotated[str, Field(min_length=1, max_length=128)]

    @field_validator("model_id")
    @classmethod
    def local_model(cls, value):
        return SelectionRequest.model_local(value)


class ToolArguments(StrictModel):
    subject: OpaqueSubject


class AgentRecord(StrictModel):
    entity_id: Identity
    timestamp: DisplayTime
    temporal_classification: TemporalClass
    provenance_status: Literal["TRACEABLE", "INCOMPLETE", "INVALID"] | None = None
    verification_status: Literal["SYNTHETIC", "UNVERIFIED_EXTERNAL", "NOT_AVAILABLE"] | None = None


class NativeToolResult(StrictModel):
    status: Literal["RETURNED_CONTEXT", "PARTIAL_CONTEXT", "INSUFFICIENT_EVIDENCE"]
    entity_ids: Annotated[list[Identity], Field(max_length=64)]
    graph_paths: Annotated[list[ProofPath], Field(max_length=8)]
    records: Annotated[list[AgentRecord], Field(max_length=8)]
    comparisons: Annotated[list[ViewComparison], Field(max_length=1)]
    gap_codes: Annotated[list[Code], Field(max_length=20)]
    truncated: bool

    @model_validator(mode="after")
    def bounded_membership(self):
        if len(self.entity_ids) != len(set(self.entity_ids)):
            raise ValueError("Duplicate result identity")
        if any(set(p.node_ids) - set(self.entity_ids) for p in self.graph_paths):
            raise ValueError("Proof path outside returned identity scope")
        if any(r.entity_id not in self.entity_ids for r in self.records):
            raise ValueError("Record outside returned identity scope")
        return self


class AgentStep(StrictModel):
    step_number: int = Field(ge=1, le=4)
    tool_name: ToolName
    parameters: ToolArguments
    subject_ids: Annotated[list[Identity], Field(min_length=1, max_length=2)]
    selected_by: Literal["DETERMINISTIC_PLAN", "LOCAL_MODEL"]
    native_query_count: int = Field(ge=1, le=8)
    result: NativeToolResult
    elapsed_ms: float = Field(ge=0, le=1e9, allow_inf_nan=False)


def canonical_agent_payload(value):
    """Runtime measurement is excluded explicitly; evidence timestamps remain part of equality."""
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        return {
            k: canonical_agent_payload(v)
            for k, v in value.items()
            if k not in {"elapsed_ms", "canonical_fingerprint"}
        }
    if isinstance(value, list):
        return [canonical_agent_payload(v) for v in value]
    return value


def canonical_agent_digest(value):
    return hashlib.sha256(canonical_json(canonical_agent_payload(value)).encode()).hexdigest()


class AgentInvestigationReport(StrictModel):
    contract_version: Literal["1.0"] = "1.0"
    incident_id: Identity
    source_fingerprint: Digest
    database_digest: Digest
    options: InvestigationOptions
    intent: Intent
    mode_executed: Literal["DETERMINISTIC_TOOL_REHEARSAL", "OLLAMA", "NONE"]
    model_requested: Annotated[str, Field(max_length=128)] | None
    model_executed: Annotated[str, Field(max_length=128)] | None
    agent_status: Literal[
        "COMPLETED",
        "PARTIAL_CONTEXT",
        "ABSTAINED",
        "MODEL_SELECTION_ONLY",
        "MODEL_UNAVAILABLE",
        "MODEL_OUTPUT_REJECTED",
        "STALE_SNAPSHOT",
        "BUDGET_EXHAUSTED",
    ]
    ai_directed_tools: bool
    ai_generated_selection: bool
    tool_trace: Annotated[list[AgentStep], Field(max_length=4)]
    validated_claims: Annotated[list[Claim], Field(max_length=10)]
    validated_citation_count: int = Field(ge=0, le=120)
    rejection_codes: Annotated[list[Code], Field(max_length=8)]
    gap_codes: Annotated[list[Code], Field(max_length=20)]
    source_truncated: bool
    model_subjects_truncated: bool
    model_interactions: int = Field(ge=0, le=5)
    native_query_count: int = Field(ge=0, le=40)
    elapsed_ms: float = Field(ge=0, le=1e9, allow_inf_nan=False)
    synthetic_notice: Annotated[str, Field(max_length=256)]
    causal_conclusion: Literal["NOT_ESTABLISHED"] = "NOT_ESTABLISHED"
    external_verification_status: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    no_cause_statement: Literal[NO_CAUSE] = NO_CAUSE
    canonical_fingerprint: Digest

    @model_validator(mode="after")
    def coherent(self):
        if self.agent_status in {
            "MODEL_SELECTION_ONLY",
            "MODEL_UNAVAILABLE",
            "MODEL_OUTPUT_REJECTED",
            "STALE_SNAPSHOT",
            "BUDGET_EXHAUSTED",
        } and (self.validated_claims or self.ai_generated_selection):
            raise ValueError("Failed/no-tool result cannot present accepted factual claims")
        if [s.step_number for s in self.tool_trace] != list(range(1, len(self.tool_trace) + 1)):
            raise ValueError("Tool trace is not consecutive")
        directed = any(s.selected_by == "LOCAL_MODEL" for s in self.tool_trace)
        if self.ai_directed_tools != directed:
            raise ValueError("AI-directed flag requires actual model-selected native steps")
        if self.mode_executed == "DETERMINISTIC_TOOL_REHEARSAL" and (
            directed
            or self.ai_generated_selection
            or self.model_requested
            or self.model_executed
            or self.model_interactions
        ):
            raise ValueError("Offline rehearsal cannot claim provider activity")
        if self.ai_generated_selection and (not directed or not self.validated_claims):
            raise ValueError("AI selection requires admitted claims and actual tool use")
        if self.validated_claims and self.validated_claims[-1].claim_type != "NO_CAUSAL_VERDICT":
            raise ValueError("Admitted claims must end in no-cause caution")
        if self.validated_citation_count != sum(len(c.citations) for c in self.validated_claims):
            raise ValueError("Citation count differs from admitted claims")
        if self.canonical_fingerprint != canonical_agent_digest(self):
            raise ValueError("Canonical report fingerprint mismatch")
        return self
