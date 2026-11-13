"""One native snapshot, existing semantic firewall, then a bounded safe browser view."""

import hashlib
import re

from traceweaver.dashboard_models import (
    ConsoleIncident,
    ConsoleIncidents,
    DashboardBundle,
    DashboardInvestigation,
    DisplayLabel,
    DisplayTime,
    ViewCandidate,
    ViewChange,
    ViewComparison,
    ViewEvent,
    ViewEvidence,
    ViewFinding,
    ViewService,
)
from traceweaver.explanation import explain_investigation
from traceweaver.explanation_catalog import fingerprint, safe_identity
from traceweaver.explanation_models import ProofPath
from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.local_files import canonical_json
from traceweaver.queries import INCIDENT_LIST
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError

PRIVATE = re.compile(
    r"[\x00-\x1f<>]|://|[A-Za-z]:[\\/]|\\\\|sk-|ghp_|"
    r"(?:password|api[_-]?key|access[_-]?token)\s*[:=]",
    re.I,
)


def display_label(value) -> DisplayLabel:
    if not isinstance(value, str) or not value or PRIVATE.search(value):
        return DisplayLabel(text="Metadata withheld", status="WITHHELD")
    return DisplayLabel(
        text=value[:157] + "..." if len(value) > 160 else value,
        status="SHORTENED" if len(value) > 160 else "RETURNED_TEXT",
    )


def display_time(value) -> DisplayTime:
    original = value.original
    allowed = isinstance(original, str) and len(original) <= 96 and not PRIVATE.search(original)
    return DisplayTime(
        utc=value.utc,
        original=original if allowed else None,
        warning_code=value.warning_code,
        original_withheld=original is not None and not allowed,
    )


def finding(value) -> ViewFinding:
    return ViewFinding(
        code=value.code,
        count=value.count,
        entity_ids=value.entity_ids[:20],
        references_omitted=len(value.entity_ids) > 20,
    )


def view_digest(view, explanation, source_fingerprint):
    return hashlib.sha256(
        canonical_json(
            {
                "investigation": view.model_dump(mode="json"),
                "explanation": explanation.model_dump(mode="json"),
                "source_fingerprint": source_fingerprint,
            }
        ).encode()
    ).hexdigest()


def bundle_from_investigation(i, options):
    effective = {
        **i.window,
        "max_candidates": i.limits["max_candidates"],
        "max_evidence": i.limits["max_evidence"],
    }
    if options.model_dump() != effective:
        raise ToolError(
            "DASHBOARD_OPTIONS_MISMATCH", "Effective source options do not match the view."
        )
    explanation = explain_investigation(i)
    source = fingerprint(i)
    if source != explanation.investigation_fingerprint:
        raise ToolError(
            "DASHBOARD_SNAPSHOT_MISMATCH", "Context changed; shared snapshot cannot be verified."
        )
    view = DashboardInvestigation(
        incident_id=i.incident_id,
        is_demo=i.is_demo,
        title=display_label(i.incident.get("title")),
        severity=display_label(i.incident.get("severity")),
        status=display_label(i.incident.get("status")),
        incident_time=display_time(i.incident_time),
        options=options,
        investigation_status=i.investigation_status,
        causal_conclusion=i.causal_conclusion,
        affected_services=[
            ViewService(id=s["id"], name=display_label(s.get("name"))) for s in i.affected_services
        ],
        candidates=[
            ViewCandidate(
                deployment_id=c.deployment_id,
                target_service_id=c.target_service_id,
                name=display_label(c.properties.get("name")),
                dependency_depth=c.dependency_depth,
                temporal_classification=c.temporal_classification,
                candidate_assessment=c.candidate_assessment,
                deployment_occurred_at=display_time(c.deployment_occurred_at),
                graph_paths=[ProofPath.model_validate(p.model_dump()) for p in c.graph_paths],
                changes=[
                    ViewChange(
                        change_id=x.change_id,
                        name=display_label(x.properties.get("name")),
                        graph_path=ProofPath.model_validate(x.graph_path.model_dump()),
                    )
                    for x in c.changes
                ],
            )
            for c in i.candidates
        ],
        evidence=[
            ViewEvidence(
                evidence_id=e.evidence_id,
                is_demo=e.is_demo,
                evidence_observed_at=display_time(e.evidence_observed_at),
                temporal_classification=e.temporal_classification,
                observed_service_ids=e.observed_service_ids,
                graph_paths=[ProofPath.model_validate(p.model_dump()) for p in e.graph_paths],
                provenance_status=e.provenance_status,
                verification_status=e.verification_status,
                warnings=[finding(w) for w in e.warnings],
                source_reference="WITHHELD" if e.source_ref is not None else "NOT_AVAILABLE",
            )
            for e in i.evidence
        ],
        contradictions=[
            ViewComparison(
                evidence_ids=c.evidence_ids,
                service_id=c.service_id,
                signal_key=display_label(c.signal_key),
                environment=display_label(c.environment),
                overlap_window=c.overlap_window,
                observed_states=c.observed_states,
                classification=c.classification,
            )
            for c in i.contradictions
        ],
        timeline=[
            ViewEvent(
                kind=e.kind,
                entity_id=e.entity_id,
                target_service_id=e.target_service_id,
                timestamp=display_time(e.timestamp),
                temporal_classification=e.temporal_classification,
            )
            for e in i.timeline
        ],
        evidence_gaps=[finding(g) for g in i.evidence_gaps],
        truncation=i.truncation,
        results_may_be_truncated=i.results_may_be_truncated,
    )
    bundle = DashboardBundle(
        source_fingerprint=source,
        view_fingerprint=view_digest(view, explanation, source),
        investigation=view,
        explanation=explanation,
    )
    if len(bundle.model_dump_json().encode()) > 2 * 1024 * 1024:
        raise ToolError("DASHBOARD_RESPONSE_LIMIT", "Context exceeds browser admission limits.")
    return bundle


def dashboard(database, incident_id, options=None):
    options = options or InvestigationOptions()
    with GraphStore(database) as store:
        investigation = investigate(store, incident_id, options)
    return bundle_from_investigation(investigation, options)


def console_incidents(database):
    with GraphStore(database) as store:
        rows = store.execute(INCIDENT_LIST, {"limit": 101})
    result = []
    omitted = 0
    for row in rows[:100]:
        if not safe_identity(row["id"]):
            omitted += 1
            continue
        labels = {field: display_label(row.get(field)) for field in ("title", "severity", "status")}
        result.append(
            ConsoleIncident(
                id=row["id"],
                **{k: v.text for k, v in labels.items()},
                metadata_withheld=any(v.status != "RETURNED_TEXT" for v in labels.values()),
            )
        )
    return ConsoleIncidents(
        incidents=result,
        results_may_be_truncated=len(rows) > 100,
        unsafe_identifiers_omitted=omitted,
    )
