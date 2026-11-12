"""Strict, lossless-to-microseconds ISO timestamp handling and explicit UTC windows."""

import re
from datetime import UTC, datetime, timedelta

from traceweaver.investigation_models import (
    InvestigationOptions,
    TemporalAssessment,
    TimestampValue,
)

ISO_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})"
)


def utc_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_timestamp(value, source_field: str = "timestamp") -> TimestampValue:
    if value is None or value == "":
        return TimestampValue(
            source_field=source_field, original=value, warning_code="MISSING_TIMESTAMP"
        )
    if not isinstance(value, str) or not ISO_TIMESTAMP.fullmatch(value) or value.endswith("-00:00"):
        return TimestampValue(
            source_field=source_field, original=value, warning_code="INVALID_TIMESTAMP"
        )
    if not value.endswith("Z") and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        return TimestampValue(
            source_field=source_field, original=value, warning_code="INVALID_TIMESTAMP"
        )
    try:
        normalized = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, OverflowError):
        return TimestampValue(
            source_field=source_field, original=value, warning_code="INVALID_TIMESTAMP"
        )
    return TimestampValue(source_field=source_field, original=value, utc=utc_text(normalized))


def entity_timestamp(properties: dict, semantic_field: str) -> TimestampValue:
    # An explicit but invalid semantic field must not fall back to another timestamp.
    field = semantic_field if semantic_field in properties else "timestamp"
    return parse_timestamp(properties.get(field), field)


def as_datetime(timestamp: TimestampValue) -> datetime | None:
    return datetime.fromisoformat(timestamp.utc.replace("Z", "+00:00")) if timestamp.utc else None


def classify_time(
    event: TimestampValue, anchor: TimestampValue, options: InvestigationOptions
) -> TemporalAssessment:
    time, start = as_datetime(event), as_datetime(anchor)
    if start is None:
        return TemporalAssessment(
            temporal_classification="UNKNOWN",
            temporal_reason="Unknown onset prevents reliable temporal exclusion.",
        )
    if time is None:
        return TemporalAssessment(
            temporal_classification="UNKNOWN",
            temporal_reason="Event time is missing or invalid; ingestion time is not substituted.",
        )
    # Compare a signed delta to avoid datetime-boundary underflow when constructing a window.
    delta = time - start
    if delta == timedelta(0):
        label, reason = "AT_ONSET", "Exactly the incident onset; not a preceding event."
    elif -timedelta(minutes=options.pre_minutes) <= delta < timedelta(0):
        label, reason = (
            "BEFORE",
            "Inside the inclusive pre-window lower bound and strictly before onset.",
        )
    elif timedelta(0) < delta <= timedelta(minutes=options.post_minutes):
        label, reason = (
            "AFTER",
            "After onset and within the inclusive post-window; not a preceding trigger.",
        )
    else:
        label, reason = "OUTSIDE_WINDOW", "Valid event time outside the requested pre/post window."
    return TemporalAssessment(temporal_classification=label, temporal_reason=reason)


def integer_query(value):
    """Reject floats, booleans and ambiguous numeric strings before integer coercion."""
    if type(value) is int or (isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value)):
        return int(value)
    raise ValueError("Expected an integer")
