"""Semantic citation firewall over an isolated copy of one Investigation snapshot."""

from traceweaver.contradictions import detect_contradictions
from traceweaver.explanation_catalog import (
    claim_id,
    fingerprint,
    gap_citation,
    graph_citation,
    provenance_citation,
    temporal_citation,
)
from traceweaver.explanation_models import AdmissibleClaimCatalog, Citation, ProofPath
from traceweaver.explanation_renderer import statement
from traceweaver.investigation_models import Investigation, InvestigationOptions
from traceweaver.temporal import classify_time, entity_timestamp
from traceweaver.tool_errors import ToolError


class CitationRejected(ToolError):
    def __init__(self, code="UNSUPPORTED_CITATION"):
        super().__init__(
            code, "Claim selection is not supported by this investigation snapshot.", 13
        )


def valid_layout(path) -> bool:
    if len(path.node_ids) != len(path.edges) + 1:
        return False
    for index, edge in enumerate(path.edges):
        left, right = path.node_ids[index : index + 2]
        if edge.traversal_direction == "REVERSE":
            if edge.type != "TARGETS":
                return False
            left, right = right, left
        if (left, right) != (edge.source_id, edge.target_id):
            return False
    return True


class CitationValidator:
    def __init__(self, investigation, catalog):
        # frozen Pydantic models alone do not freeze nested lists. Own deep copies instead.
        self._source = Investigation.model_validate_json(investigation.model_dump_json())
        self._catalog = AdmissibleClaimCatalog.model_validate_json(catalog.model_dump_json())
        self._fingerprint = fingerprint(self._source)
        if (
            self._catalog.investigation_fingerprint != self._fingerprint
            or self._catalog.incident_id != self._source.incident_id
        ):
            raise CitationRejected("SNAPSHOT_MISMATCH")
        self._claims = {claim.claim_id: claim for claim in self._catalog.claims}
        if len(self._claims) != len(self._catalog.claims):
            raise CitationRejected("DUPLICATE_CATALOG_ID")

    def validate(self, selected_ids: list[str], snapshot: str, *, require_caution=True):
        if snapshot != self._fingerprint:
            raise CitationRejected("SNAPSHOT_MISMATCH")
        if not isinstance(selected_ids, list) or not 1 <= len(selected_ids) <= 10:
            raise CitationRejected("SELECTION_COUNT")
        if any(not isinstance(value, str) for value in selected_ids):
            raise CitationRejected("INVALID_CLAIM_ID")
        if len(set(selected_ids)) != len(selected_ids):
            raise CitationRejected("DUPLICATE_CLAIM_ID")
        if any(value not in self._claims for value in selected_ids):
            raise CitationRejected("UNKNOWN_CLAIM_ID")
        claims = [self._claims[value] for value in selected_ids]
        if require_caution and not any(c.claim_type == "NO_CAUSAL_VERDICT" for c in claims):
            raise CitationRejected("MISSING_CAUSAL_CAUTION")
        for claim in claims:
            self._validate_claim(claim)
        return [claim.model_copy(deep=True) for claim in claims]

    def _validate_claim(self, claim):
        i = self._source
        kind, ids, citations = claim.claim_type, claim.referenced_entity_ids, claim.citations
        qualifier = citations[0].code if kind == "CONTEXT_GAP" else ""
        if claim.claim_id != claim_id(kind, ids, qualifier):
            raise CitationRejected("CLAIM_ID_MISMATCH")
        expected = None
        if (
            kind == "NO_CAUSAL_VERDICT"
            and ids == [i.incident_id]
            and i.causal_conclusion == "NOT_ESTABLISHED"
        ):
            expected = [Citation(kind="GAP", entity_ids=ids, code="NO_CAUSAL_VERDICT")]
        elif (
            kind == "INCIDENT_OBSERVED"
            and ids == [i.incident_id]
            and i.incident.get("id") == i.incident_id
        ):
            anchor = entity_timestamp(i.incident, "incident_started_at")
            if anchor.utc != i.incident_time.utc:
                raise CitationRejected("INVALID_TEMPORAL_SUPPORT")
            expected = [Citation(kind="INCIDENT", entity_ids=ids, event_utc=anchor.utc)]
        elif kind == "SERVICE_AFFECTED" and len(ids) == 2 and ids[0] == i.incident_id:
            if any(service.get("id") == ids[1] for service in i.affected_services):
                path = ProofPath(
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
                expected = [graph_citation(path)]
        elif kind in {
            "DEPLOYMENT_CONNECTED",
            "DEPLOYMENT_BEFORE_ONSET",
            "DEPLOYMENT_NOT_PRECEDING",
        }:
            candidate = next(
                (c for c in i.candidates if ids == [c.deployment_id, c.target_service_id]), None
            )
            if candidate and candidate.graph_paths:
                path = candidate.graph_paths[0]
                if (
                    path.node_ids[0] != i.incident_id
                    or path.node_ids[-2:] != [ids[1], ids[0]]
                    or path.edges[0].type != "AFFECTS"
                    or path.edges[-1].type != "TARGETS"
                    or path.edges[-1].traversal_direction != "REVERSE"
                ):
                    raise CitationRejected("INVALID_CANDIDATE_PATH")
                expected = [graph_citation(path)]
                if kind != "DEPLOYMENT_CONNECTED":
                    event = entity_timestamp(candidate.properties, "deployment_occurred_at")
                    anchor = entity_timestamp(i.incident, "incident_started_at")
                    options = InvestigationOptions(**i.window)
                    category = classify_time(event, anchor, options).temporal_classification
                    permitted = (
                        {"BEFORE"} if kind == "DEPLOYMENT_BEFORE_ONSET" else {"AT_ONSET", "AFTER"}
                    )
                    if (
                        category not in permitted
                        or category != candidate.temporal_classification
                        or not event.utc
                        or event.utc != candidate.deployment_occurred_at.utc
                    ):
                        raise CitationRejected("INVALID_TEMPORAL_SUPPORT")
                    expected.append(temporal_citation(candidate))
        elif kind in {"EVIDENCE_REPORTED", "SOURCE_UNVERIFIED"}:
            evidence = next((e for e in i.evidence if ids == [e.evidence_id]), None)
            if evidence and (
                kind != "SOURCE_UNVERIFIED" or evidence.verification_status == "UNVERIFIED_EXTERNAL"
            ):
                path = evidence.graph_paths[0]
                if (
                    path.node_ids[:2] != [i.incident_id, evidence.evidence_id]
                    or path.edges[0].type != "HAS_EVIDENCE"
                    or any(
                        e.type == "OBSERVED_ON" and e.target_id not in evidence.observed_service_ids
                        for e in path.edges
                    )
                ):
                    raise CitationRejected("INVALID_EVIDENCE_SCOPE")
                expected = [
                    Citation(kind="EVIDENCE", entity_ids=ids),
                    graph_citation(path),
                    provenance_citation(evidence),
                ]
        elif kind in {"STRUCTURED_CONFLICT", "COMPARISON_UNDETERMINED"}:
            category = (
                "CONFLICTING_OBSERVATIONS" if kind == "STRUCTURED_CONFLICT" else "UNDETERMINED"
            )
            pair = next(
                (
                    p
                    for p in i.contradictions
                    if sorted(p.evidence_ids) == ids and p.classification == category
                ),
                None,
            )
            # Reuse the proven comparison rules independently of catalog generation.
            comparable, _, _ = detect_contradictions(i.evidence)
            if pair and pair in comparable:
                evidence = {e.evidence_id: e for e in i.evidence}
                expected = [
                    Citation(
                        kind="CONTRADICTION",
                        entity_ids=ids + [pair.service_id],
                        classification=category,
                        overlap_start=pair.overlap_window["start"],
                        overlap_end=pair.overlap_window["end"],
                    )
                ]
                expected += [
                    graph_citation(
                        next(
                            path
                            for path in evidence[e].graph_paths
                            if path.node_ids[-1] == pair.service_id
                            and path.edges[-1].type == "OBSERVED_ON"
                        )
                    )
                    for e in ids
                ]
        elif kind == "CONTEXT_GAP":
            gaps = {g.code: g for g in i.evidence_gaps + i.limitations}
            gap = gaps.get(qualifier)
            if gap:
                copy = gap.model_copy(deep=True)
                if not copy.entity_ids:
                    copy.entity_ids = [i.incident_id]
                if ids == copy.entity_ids[:12]:
                    expected = [gap_citation(copy)]
        if expected is None or citations != expected:
            raise CitationRejected()
        if any(c.graph_path and not valid_layout(c.graph_path) for c in citations):
            raise CitationRejected("INVALID_EDGE_DIRECTION")
        if claim.statement != statement(kind, ids, expected):
            raise CitationRejected("UNTRUSTED_STATEMENT")
