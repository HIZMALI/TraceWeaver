"""Compare explicit graph-grounded observations, never keywords in narrative text."""

from dataclasses import dataclass
from datetime import datetime
from itertools import combinations

from traceweaver.investigation_models import (
    Contradiction,
    ContradictionAudit,
    EvidenceContext,
    Finding,
)
from traceweaver.temporal import as_datetime, parse_timestamp, utc_text

STATES = {"HEALTHY", "DEGRADED", "FAILED"}


@dataclass(frozen=True)
class Observation:
    evidence_id: str
    service_id: str
    signal_key: str
    environment: str
    state: str
    start: datetime
    end: datetime


def structured_observation(item: EvidenceContext) -> tuple[Observation | None, str | None]:
    data = item.properties
    required = ("signal_key", "observed_state", "service_id", "environment")
    if any(key not in data for key in required):
        return None, "MISSING_STRUCTURED_SIGNAL"
    if any(not isinstance(data[key], str) or not data[key].strip() for key in required):
        return None, "INVALID_STRUCTURED_SIGNAL"
    if data["observed_state"] not in STATES or data["service_id"] not in item.observed_service_ids:
        return None, "INVALID_STRUCTURED_CONTEXT"
    if "observation_window_start" in data or "observation_window_end" in data:
        start = as_datetime(parse_timestamp(data.get("observation_window_start")))
        end = as_datetime(parse_timestamp(data.get("observation_window_end")))
    else:
        start = end = as_datetime(item.evidence_observed_at)
    if start is None or end is None or start > end:
        return None, "INVALID_OBSERVATION_WINDOW"
    return Observation(
        item.evidence_id,
        data["service_id"],
        data["signal_key"],
        data["environment"],
        data["observed_state"],
        start,
        end,
    ), None


def detect_contradictions(
    evidence: list[EvidenceContext],
) -> tuple[list[Contradiction], ContradictionAudit, bool]:
    observations, warnings = [], []
    for item in evidence:
        observation, code = structured_observation(item)
        if observation:
            observations.append(observation)
        else:
            warnings.append(
                Finding(
                    code=code,
                    message="Evidence is not evaluable for structured comparisons.",
                    entity_ids=[item.evidence_id],
                )
            )
    results = []
    comparable = conflicts = undetermined = 0
    for left, right in combinations(observations, 2):
        if (left.service_id, left.signal_key, left.environment) != (
            right.service_id,
            right.signal_key,
            right.environment,
        ):
            continue
        start, end = max(left.start, right.start), min(left.end, right.end)
        if start > end:
            continue
        comparable += 1
        if left.state == right.state:
            continue
        conflict = {left.state, right.state} == {"HEALTHY", "FAILED"}
        conflicts += int(conflict)
        undetermined += int(not conflict)
        if len(results) < 100:
            results.append(
                Contradiction(
                    evidence_ids=[left.evidence_id, right.evidence_id],
                    signal_key=left.signal_key,
                    service_id=left.service_id,
                    environment=left.environment,
                    overlap_window={"start": utc_text(start), "end": utc_text(end)},
                    observed_states=[left.state, right.state],
                    classification="CONFLICTING_OBSERVATIONS" if conflict else "UNDETERMINED",
                    reason=(
                        "Opposite states share graph-grounded context and overlapping time."
                        if conflict
                        else "DEGRADED versus a different state has no declared opposition rule."
                    ),
                )
            )
    return (
        results,
        ContradictionAudit(
            evaluable_evidence_count=len(observations),
            not_evaluable_count=len(warnings),
            comparable_pair_count=comparable,
            conflict_count=conflicts,
            undetermined_count=undetermined,
            warnings=warnings[:100],
        ),
        conflicts + undetermined > 100,
    )
