"""Bounded admissible propositions from one returned real-graph Investigation."""

import hashlib
import re

from traceweaver.explanation_models import AdmissibleClaimCatalog, Citation, Claim, ProofPath
from traceweaver.explanation_renderer import statement
from traceweaver.local_files import canonical_json
from traceweaver.tool_errors import ToolError

CATALOG_CAP = 128
MAX_CONTEXT_BYTES = 8 * 1024 * 1024
CLAIM_ORDER = [
    "NO_CAUSAL_VERDICT",
    "INCIDENT_OBSERVED",
    "CONTEXT_GAP",
    "STRUCTURED_CONFLICT",
    "COMPARISON_UNDETERMINED",
    "SOURCE_UNVERIFIED",
    "SERVICE_AFFECTED",
    "DEPLOYMENT_CONNECTED",
    "DEPLOYMENT_BEFORE_ONSET",
    "DEPLOYMENT_NOT_PRECEDING",
    "EVIDENCE_REPORTED",
]


def safe_identity(value) -> bool:
    return (
        isinstance(value, str)
        and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value))
        and not re.search(r"(?i)(?:sk-|ghp_|AKIA|password|access_token|api_key)", value)
    )


def fingerprint(investigation) -> str:
    data = canonical_json(
        {
            "investigation": investigation.model_dump(mode="json"),
            "effective_options": {
                **investigation.window,
                "max_candidates": investigation.limits["max_candidates"],
                "max_evidence": investigation.limits["max_evidence"],
            },
        }
    ).encode()
    if len(data) > MAX_CONTEXT_BYTES:
        raise ToolError(
            "CONTEXT_SIZE_LIMIT", "Returned context exceeds explanation admission limits."
        )
    return hashlib.sha256(data).hexdigest()


def claim_id(kind: str, ids: list[str], qualifier: str = "") -> str:
    key = canonical_json({"kind": kind, "ids": ids, "qualifier": qualifier})
    return "C-" + hashlib.sha256(key.encode()).hexdigest()[:24]


def graph_citation(path) -> Citation:
    proof = ProofPath.model_validate(path.model_dump())
    return Citation(kind="GRAPH_PATH", entity_ids=proof.node_ids, graph_path=proof)


def provenance_citation(evidence) -> Citation:
    return Citation(
        kind="PROVENANCE",
        entity_ids=[evidence.evidence_id],
        provenance_status=evidence.provenance_status,
        verification_status=evidence.verification_status,
        source_ref_withheld=evidence.source_ref is not None,
    )


def temporal_citation(candidate) -> Citation:
    return Citation(
        kind="TEMPORAL",
        entity_ids=[candidate.deployment_id, candidate.target_service_id],
        event_utc=candidate.deployment_occurred_at.utc,
        temporal_classification=candidate.temporal_classification,
    )


def gap_citation(gap) -> Citation:
    return Citation(kind="GAP", entity_ids=gap.entity_ids[:12], code=gap.code, count=gap.count)


def make_claim(kind, ids, citations, qualifier="") -> Claim:
    if not all(
        safe_identity(value) for value in ids + [v for c in citations for v in c.entity_ids]
    ):
        raise ToolError("UNSAFE_CONTEXT_IDENTIFIER", "Context has unsupported display identifiers.")
    return Claim(
        claim_id=claim_id(kind, ids, qualifier),
        claim_type=kind,
        referenced_entity_ids=ids,
        citations=citations,
        statement=statement(kind, ids, citations),
    )


def build_catalog(investigation) -> AdmissibleClaimCatalog:
    i = investigation
    claims = [
        make_claim(
            "NO_CAUSAL_VERDICT",
            [i.incident_id],
            [Citation(kind="GAP", entity_ids=[i.incident_id], code="NO_CAUSAL_VERDICT")],
        )
    ]
    claims.append(
        make_claim(
            "INCIDENT_OBSERVED",
            [i.incident_id],
            [Citation(kind="INCIDENT", entity_ids=[i.incident_id], event_utc=i.incident_time.utc)],
        )
    )
    for service in i.affected_services:
        ids = [i.incident_id, service["id"]]
        proof = ProofPath(
            node_ids=ids,
            edges=[
                {
                    "type": "AFFECTS",
                    "source_id": ids[0],
                    "target_id": ids[1],
                    "traversal_direction": "FORWARD",
                }
            ],
        )
        claims.append(make_claim("SERVICE_AFFECTED", ids, [graph_citation(proof)]))
    for candidate in i.candidates:
        ids = [candidate.deployment_id, candidate.target_service_id]
        paths = [graph_citation(candidate.graph_paths[0])]
        claims.append(make_claim("DEPLOYMENT_CONNECTED", ids, paths))
        category = candidate.temporal_classification
        if category in {"BEFORE", "AT_ONSET", "AFTER"} and i.incident_time.utc:
            kind = "DEPLOYMENT_BEFORE_ONSET" if category == "BEFORE" else "DEPLOYMENT_NOT_PRECEDING"
            claims.append(make_claim(kind, ids, paths + [temporal_citation(candidate)]))
    for evidence in i.evidence:
        ids = [evidence.evidence_id]
        citations = [
            Citation(kind="EVIDENCE", entity_ids=ids),
            graph_citation(evidence.graph_paths[0]),
            provenance_citation(evidence),
        ]
        claims.append(make_claim("EVIDENCE_REPORTED", ids, citations))
        if evidence.verification_status == "UNVERIFIED_EXTERNAL":
            claims.append(make_claim("SOURCE_UNVERIFIED", ids, citations))
    evidence_by_id = {e.evidence_id: e for e in i.evidence}
    for pair in i.contradictions:
        ids = sorted(pair.evidence_ids)
        citations = [
            Citation(
                kind="CONTRADICTION",
                entity_ids=ids + [pair.service_id],
                classification=pair.classification,
                overlap_start=pair.overlap_window["start"],
                overlap_end=pair.overlap_window["end"],
            )
        ]
        citations += [
            graph_citation(
                next(
                    path
                    for path in evidence_by_id[e].graph_paths
                    if path.node_ids[-1] == pair.service_id and path.edges[-1].type == "OBSERVED_ON"
                )
            )
            for e in ids
        ]
        kind = (
            "STRUCTURED_CONFLICT"
            if pair.classification == "CONFLICTING_OBSERVATIONS"
            else "COMPARISON_UNDETERMINED"
        )
        claims.append(make_claim(kind, ids, citations))
    for gap in {g.code: g for g in i.evidence_gaps + i.limitations}.values():
        # Some source findings summarize a category without enumerating an entity.
        copy = gap.model_copy(deep=True)
        if not copy.entity_ids:
            copy.entity_ids = [i.incident_id]
        claims.append(
            make_claim("CONTEXT_GAP", copy.entity_ids[:12], [gap_citation(copy)], gap.code)
        )
    # Round-robin types prevent a large candidate list from exhausting the evidence budget.
    groups = {
        kind: sorted([c for c in claims if c.claim_type == kind], key=lambda c: c.claim_id)
        for kind in CLAIM_ORDER
    }
    ordered = []
    while any(groups.values()):
        for kind in CLAIM_ORDER:
            if groups[kind]:
                ordered.append(groups[kind].pop(0))
    return AdmissibleClaimCatalog(
        investigation_fingerprint=fingerprint(i),
        incident_id=i.incident_id,
        claims=ordered[:CATALOG_CAP],
        generated_count=len(ordered),
        truncated=len(ordered) > CATALOG_CAP,
    )


def select_deterministically(catalog) -> list[str]:
    chosen = []
    # Reserve one final slot for the mandatory caution.
    for kind, count in [
        ("INCIDENT_OBSERVED", 1),
        ("SERVICE_AFFECTED", 1),
        ("DEPLOYMENT_CONNECTED", 2),
        ("DEPLOYMENT_NOT_PRECEDING", 1),
        ("DEPLOYMENT_BEFORE_ONSET", 1),
        ("EVIDENCE_REPORTED", 1),
        ("STRUCTURED_CONFLICT", 1),
        ("COMPARISON_UNDETERMINED", 1),
        ("CONTEXT_GAP", 1),
        ("SOURCE_UNVERIFIED", 1),
    ]:
        chosen.extend([c.claim_id for c in catalog.claims if c.claim_type == kind][:count])
    caution = next(c.claim_id for c in catalog.claims if c.claim_type == "NO_CAUSAL_VERDICT")
    return chosen[:9] + [caution]
