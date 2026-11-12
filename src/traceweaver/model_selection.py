"""A provider can select opaque existing IDs, never supply factual prose or citations."""

import re
from typing import Annotated, Literal

from pydantic import Field, ValidationError, model_validator

from traceweaver.citation_validator import CitationRejected, CitationValidator
from traceweaver.explanation_models import ClaimId, Digest, StrictModel
from traceweaver.local_files import canonical_json, parse_json_document
from traceweaver.tool_errors import ToolError

MAX_PROPOSAL_BYTES = 4096
MAX_PROMPT_BYTES = 32768


class ModelProposal(StrictModel):
    investigation_fingerprint: Digest
    selected_claim_ids: Annotated[list[ClaimId], Field(max_length=8)]
    focus: Literal["TIMELINE", "DEPENDENCIES", "EVIDENCE", "GAPS", "BALANCED"]
    abstain: bool

    @model_validator(mode="after")
    def admissible_shape(self):
        if self.abstain and self.selected_claim_ids:
            raise ValueError("Abstention must select no factual claims")
        if not self.abstain and not self.selected_claim_ids:
            raise ValueError("Selection cannot be empty without abstention")
        if len(set(self.selected_claim_ids)) != len(self.selected_claim_ids):
            raise ValueError("Duplicate claim IDs are not allowed")
        return self


def valid_model_id(value) -> bool:
    return (
        isinstance(value, str)
        and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./:-]{0,127}", value))
        and "cloud" not in value.lower()
        and ".." not in value
        and not value.startswith(("http:", "https:"))
    )


def sanitized_packet(catalog) -> dict:
    # Not even raw stable entity IDs are sent: IDs themselves may contain private material.
    packet = {
        "investigation_fingerprint": catalog.investigation_fingerprint,
        "task": "Select and order 3 to 8 existing claim IDs, or abstain with an empty list. "
        "Select fewer only if fewer than three catalog entries exist. No factual prose.",
        "claims": [
            {
                "claim_id": c.claim_id,
                "claim_type": c.claim_type,
                "citation_kinds": [citation.kind for citation in c.citations],
                "temporal_classification": next(
                    (p.temporal_classification for p in c.citations if p.kind == "TEMPORAL"), None
                ),
                "verification_status": next(
                    (p.verification_status for p in c.citations if p.kind == "PROVENANCE"), None
                ),
            }
            for c in catalog.claims
        ],
    }
    if len(canonical_json(packet).encode()) > MAX_PROMPT_BYTES:
        # Explicitly cap the offered subset, preserving the mandatory caution entry.
        packet["claims"] = packet["claims"][:64]
    if len(canonical_json(packet).encode()) > MAX_PROMPT_BYTES:
        raise CitationRejected("MODEL_PROMPT_LIMIT")
    return packet


def accept_proposal(raw: bytes, investigation, catalog, offered_ids=None):
    if not isinstance(raw, bytes) or len(raw) > MAX_PROPOSAL_BYTES:
        raise CitationRejected("MODEL_PROPOSAL_LIMIT")
    try:
        proposal = ModelProposal.model_validate(parse_json_document(raw, max_depth=4))
    except (ValidationError, ToolError):
        raise CitationRejected("MODEL_PROPOSAL_SCHEMA") from None
    if proposal.investigation_fingerprint != catalog.investigation_fingerprint:
        raise CitationRejected("SNAPSHOT_MISMATCH")
    offered = set(offered_ids if offered_ids is not None else [c.claim_id for c in catalog.claims])
    if any(value not in offered for value in proposal.selected_claim_ids):
        raise CitationRejected("UNKNOWN_CLAIM_ID")
    if not proposal.abstain and len(proposal.selected_claim_ids) < min(3, len(offered)):
        raise CitationRejected("SELECTION_COUNT")
    ids = list(proposal.selected_claim_ids)
    caution = next(c.claim_id for c in catalog.claims if c.claim_type == "NO_CAUSAL_VERDICT")
    # Caution is always the concluding claim; no invalid ID has been repaired or replaced.
    ids = [value for value in ids if value != caution] + [caution]
    claims = CitationValidator(investigation, catalog).validate(
        ids, proposal.investigation_fingerprint
    )
    return claims, proposal.abstain
