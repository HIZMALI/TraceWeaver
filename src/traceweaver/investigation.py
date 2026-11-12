"""One deterministic read-only investigation service shared by HTTP and CLI."""

from datetime import UTC, datetime

from traceweaver.contradictions import detect_contradictions
from traceweaver.investigation_models import (
    Candidate,
    ChangeContext,
    DataQuality,
    Finding,
    GraphEdge,
    GraphPath,
    Investigation,
    InvestigationOptions,
    TimelineEvent,
)
from traceweaver.provenance import audit_provenance, evidence_context, graph_properties
from traceweaver.queries import (
    AFFECTED_SERVICES,
    INCIDENT_LOOKUP,
    INVESTIGATION_CANDIDATES,
    INVESTIGATION_CHANGES,
    INVESTIGATION_EVIDENCE,
    INVESTIGATION_OBSERVATIONS,
    IncidentNotFound,
)
from traceweaver.storage import GraphStore, QueryError
from traceweaver.temporal import as_datetime, classify_time, entity_timestamp

LIST_CAP = 100
CATEGORY_ORDER = {
    name: n for n, name in enumerate(("BEFORE", "AT_ONSET", "AFTER", "OUTSIDE_WINDOW", "UNKNOWN"))
}
LAST_TIME = datetime.max.replace(tzinfo=UTC)


def _bounded(store: GraphStore, query: str, params: dict, limit: int = LIST_CAP):
    rows = store.execute(query, {**params, "limit": limit + 1})
    return rows[:limit], len(rows) > limit


def _id(value) -> str:
    if not isinstance(value, str) or not value:
        raise QueryError("Investigation graph entities require stable string IDs")
    return value


def candidate_path(node_ids: list) -> GraphPath:
    ids = [_id(value) for value in node_ids]
    edges = [GraphEdge(type="AFFECTS", source_id=ids[0], target_id=ids[1])]
    edges += [
        GraphEdge(type="DEPENDS_ON", source_id=source, target_id=target)
        for source, target in zip(ids[1:-2], ids[2:-1], strict=True)
    ]
    edges.append(
        GraphEdge(
            type="TARGETS", source_id=ids[-1], target_id=ids[-2], traversal_direction="REVERSE"
        )
    )
    return GraphPath(node_ids=ids, edges=edges)


def investigate(
    store: GraphStore,
    incident_id: str,
    options: InvestigationOptions | None = None,
) -> Investigation:
    options = options or InvestigationOptions()
    params = {"incident_id": incident_id}
    incident_rows = store.execute(INCIDENT_LOOKUP, params)
    if not incident_rows:
        raise IncidentNotFound(incident_id)
    incident = graph_properties(incident_rows[0]["incident"])
    _id(incident.get("id"))
    anchor = entity_timestamp(incident, "incident_started_at")
    affected_rows, affected_cut = _bounded(store, AFFECTED_SERVICES, params)
    candidate_rows, candidate_cut = _bounded(
        store, INVESTIGATION_CANDIDATES, params, options.max_candidates
    )
    evidence_rows, evidence_cut = _bounded(
        store, INVESTIGATION_EVIDENCE, params, options.max_evidence
    )
    deployment_ids = sorted({_id(row["deployment"].get("id")) for row in candidate_rows})
    evidence_ids = [_id(row["evidence"].get("id")) for row in evidence_rows]
    change_rows, changes_cut = (
        _bounded(store, INVESTIGATION_CHANGES, {"deployment_ids": deployment_ids})
        if deployment_ids
        else ([], False)
    )
    observation_rows, observations_cut = (
        _bounded(store, INVESTIGATION_OBSERVATIONS, {**params, "evidence_ids": evidence_ids})
        if evidence_ids
        else ([], False)
    )

    candidates = []
    for row in candidate_rows:
        deployment = graph_properties(row["deployment"])
        deployment_id = _id(deployment.get("id"))
        path = candidate_path(row["node_ids"])
        changes = []
        for change_row in change_rows:
            if change_row["deployment_id"] == deployment_id:
                change = graph_properties(change_row["change"])
                change_id = _id(change.get("id"))
                changes.append(
                    ChangeContext(
                        change_id=change_id,
                        properties=change,
                        graph_path=GraphPath(
                            node_ids=path.node_ids + [change_id],
                            edges=path.edges
                            + [
                                GraphEdge(
                                    type="INCLUDES_CHANGE",
                                    source_id=deployment_id,
                                    target_id=change_id,
                                )
                            ],
                        ),
                    )
                )
        timestamp = entity_timestamp(deployment, "deployment_occurred_at")
        assessment = classify_time(timestamp, anchor, options)
        category = assessment.temporal_classification
        candidates.append(
            Candidate(
                deployment_id=deployment_id,
                target_service_id=_id(row["target"].get("id")),
                change_ids=[change.change_id for change in changes],
                changes=changes,
                dependency_depth=row["dependency_depth"],
                deployment_occurred_at=timestamp,
                candidate_assessment=(
                    "INVESTIGATE"
                    if category == "BEFORE"
                    else "INSUFFICIENT_DATA"
                    if category == "UNKNOWN"
                    else "TEMPORALLY_EXCLUDED"
                ),
                assessment_reason=(
                    "Pre-window topology merits review; causation is not established."
                    if category == "BEFORE"
                    else "Unknown event time or onset prevents temporal eligibility assessment."
                    if category == "UNKNOWN"
                    else "Excluded only as a preceding trigger; retained as contextual information."
                ),
                graph_paths=[path],
                properties=deployment,
                **assessment.model_dump(),
            )
        )
    candidates.sort(
        key=lambda c: (
            CATEGORY_ORDER[c.temporal_classification],
            c.dependency_depth,
            as_datetime(c.deployment_occurred_at) or LAST_TIME,
            c.deployment_id,
            c.target_service_id,
        )
    )
    observations = {}
    for row in observation_rows:
        observations.setdefault(_id(row["evidence_id"]), []).append(_id(row["service_id"]))
    evidence = [
        evidence_context(
            incident_id,
            graph_properties(row["evidence"]),
            sorted(set(observations.get(row["evidence"]["id"], []))),
            anchor,
            options,
        )
        for row in evidence_rows
    ]
    provenance = audit_provenance(evidence)
    contradictions, contradiction_audit, contradictions_cut = detect_contradictions(evidence)
    timeline = [
        TimelineEvent(
            kind="INCIDENT",
            entity_id=incident_id,
            timestamp=anchor,
            **classify_time(anchor, anchor, options).model_dump(),
        )
    ]
    timeline += [
        TimelineEvent(
            kind="DEPLOYMENT",
            entity_id=c.deployment_id,
            target_service_id=c.target_service_id,
            timestamp=c.deployment_occurred_at,
            temporal_classification=c.temporal_classification,
            temporal_reason=c.temporal_reason,
        )
        for c in candidates
    ]
    timeline += [
        TimelineEvent(
            kind="EVIDENCE",
            entity_id=e.evidence_id,
            timestamp=e.evidence_observed_at,
            temporal_classification=e.temporal_classification,
            temporal_reason=e.temporal_reason,
        )
        for e in evidence
    ]
    timeline.sort(
        key=lambda event: (
            as_datetime(event.timestamp) or LAST_TIME,
            event.kind,
            event.entity_id,
            event.target_service_id or "",
        )
    )
    truncation = {
        "candidates": candidate_cut,
        "evidence": evidence_cut,
        "affected_services": affected_cut,
        "changes": changes_cut,
        "observations": observations_cut,
        "timeline": len(timeline) > LIST_CAP,
        "contradictions": contradictions_cut,
        "provenance_warnings": provenance.warnings_may_be_truncated,
    }
    gaps = []
    if anchor.warning_code:
        gaps.append(
            Finding(
                code=anchor.warning_code,
                entity_ids=[incident_id],
                message="Incident onset is unknown; temporal exclusions are not reliable.",
            )
        )
    bad_times = [c.deployment_id for c in candidates if not c.deployment_occurred_at.utc]
    bad_times += [e.evidence_id for e in evidence if not e.evidence_observed_at.utc]
    if bad_times:
        gaps.append(
            Finding(
                code="UNKNOWN_EVENT_TIMES",
                entity_ids=sorted(set(bad_times))[:100],
                count=len(bad_times),
                message="Event times are missing or invalid.",
            )
        )
    provenance_issues = [e.evidence_id for e in evidence if e.provenance_status != "TRACEABLE"]
    if provenance_issues:
        gaps.append(
            Finding(
                code="INCOMPLETE_PROVENANCE",
                entity_ids=provenance_issues,
                count=len(provenance_issues),
                message="Review source, time, and service-link warnings.",
            )
        )
    if contradiction_audit.not_evaluable_count:
        gaps.append(
            Finding(
                code="STRUCTURED_SIGNAL_GAPS",
                count=contradiction_audit.not_evaluable_count,
                entity_ids=[w.entity_ids[0] for w in contradiction_audit.warnings],
                message="Structured signal comparisons cannot evaluate these observations.",
            )
        )
    if not evidence:
        gaps.append(
            Finding(
                code="NO_INCIDENT_EVIDENCE",
                entity_ids=[incident_id],
                message="No incident-scoped evidence returned; this does not rule out a problem.",
            )
        )
    if not affected_rows:
        gaps.append(
            Finding(
                code="NO_AFFECTED_SERVICES",
                entity_ids=[incident_id],
                message="No AFFECTS service link was returned.",
            )
        )
    missing_changes = sorted({c.deployment_id for c in candidates if not c.changes})
    if missing_changes:
        gaps.append(
            Finding(
                code="MISSING_DEPLOYMENT_CHANGES",
                entity_ids=missing_changes,
                count=len(missing_changes),
                message="Candidates are retained without returned change links.",
            )
        )
    if contradiction_audit.conflict_count or contradiction_audit.undetermined_count:
        gaps.append(
            Finding(
                code="OBSERVATIONS_REQUIRE_RECONCILIATION",
                entity_ids=sorted({i for c in contradictions for i in c.evidence_ids}),
                count=contradiction_audit.conflict_count + contradiction_audit.undetermined_count,
                message="Reconcile conflicting or undetermined observations without blame.",
            )
        )
    if any(truncation.values()):
        gaps.append(
            Finding(
                code="TRUNCATED_CONTEXT",
                entity_ids=[incident_id],
                message="Lookahead exceeded a cap; omitted context may change this assessment.",
            )
        )
    limitations = list(gaps)
    if provenance.unverified_external_count:
        limitations.append(
            Finding(
                code="UNVERIFIED_EXTERNAL_SOURCES",
                message="External references were not contacted or verified.",
                count=provenance.unverified_external_count,
                entity_ids=[
                    e.evidence_id
                    for e in evidence
                    if e.verification_status == "UNVERIFIED_EXTERNAL"
                ],
            )
        )
    gaps.sort(key=lambda gap: gap.code)
    limitations.sort(key=lambda limitation: limitation.code)
    next_checks = [
        f"Resolve {gap.code} for {', '.join(gap.entity_ids) or incident_id}: {gap.message}"
        for gap in gaps
    ]
    if provenance.unverified_external_count:
        next_checks.append(
            "Check external sources independently; traceability is not truth verification."
        )
    unknown_times = int(anchor.utc is None) + len(bad_times)
    invalid_metadata = provenance.invalid_count > 0 or any(
        time.warning_code == "INVALID_TIMESTAMP"
        for time in [
            anchor,
            *(c.deployment_occurred_at for c in candidates),
            *(e.evidence_observed_at for e in evidence),
        ]
    )
    status = (
        "INSUFFICIENT_EVIDENCE"
        if not evidence
        else "PARTIAL_CONTEXT"
        if gaps
        else "READY_FOR_REVIEW"
    )
    demo = incident.get("demo")
    return Investigation(
        incident_id=incident_id,
        is_demo=demo if type(demo) is bool else None,
        incident=incident,
        incident_started_at=anchor.utc,
        incident_time=anchor,
        window={"pre_minutes": options.pre_minutes, "post_minutes": options.post_minutes},
        limits={
            "max_candidates": options.max_candidates,
            "max_evidence": options.max_evidence,
            "dependency_depth": 3,
            "auxiliary_lists": LIST_CAP,
        },
        affected_services=[graph_properties(row["service"]) for row in affected_rows],
        candidates=candidates,
        evidence=evidence,
        provenance_audit=provenance,
        contradictions=contradictions,
        contradiction_audit=contradiction_audit,
        timeline=timeline[:LIST_CAP],
        data_quality=DataQuality(
            status="INVALID"
            if invalid_metadata
            else "INCOMPLETE"
            if unknown_times or provenance_issues or any(truncation.values())
            else "COMPLETE",
            unknown_timestamp_count=unknown_times,
            provenance_issue_count=len(provenance_issues),
            structured_evidence_not_evaluable_count=contradiction_audit.not_evaluable_count,
        ),
        investigation_status=status,
        status_reasons=[gap.code for gap in gaps],
        limitations=limitations,
        evidence_gaps=gaps,
        next_checks=next_checks,
        truncation=truncation,
        results_may_be_truncated=any(truncation.values()),
        demo_notice=(
            "Synthetic demo data; no real incident or causal finding."
            if demo is True
            else "Demo status is not established as synthetic; source claims remain unverified."
            if type(demo) is not bool
            else "Source metadata is not independent verification of a real incident."
        ),
    )
