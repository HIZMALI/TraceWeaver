import pytest
from pydantic import ValidationError

from traceweaver.investigation_models import InvestigationOptions
from traceweaver.temporal import classify_time, entity_timestamp, parse_timestamp


@pytest.mark.parametrize(
    ("time", "expected"),
    [
        ("2026-11-12T08:00:00Z", "BEFORE"),
        ("2026-11-12T07:59:59Z", "OUTSIDE_WINDOW"),
        ("2026-11-12T09:59:59Z", "BEFORE"),
        ("2026-11-12T10:00:00Z", "AT_ONSET"),
        ("2026-11-12T10:00:01Z", "AFTER"),
        ("2026-11-12T10:30:00Z", "AFTER"),
        ("2026-11-12T10:30:01Z", "OUTSIDE_WINDOW"),
    ],
)
def test_exact_window_boundaries(time, expected):
    assessment = classify_time(
        parse_timestamp(time), parse_timestamp("2026-11-12T10:00:00Z"), InvestigationOptions()
    )
    assert assessment.temporal_classification == expected


def test_zero_window_only_accepts_exact_onset():
    anchor = parse_timestamp("2026-11-12T10:00:00Z")
    options = InvestigationOptions(pre_minutes=0, post_minutes=0)
    assert classify_time(anchor, anchor, options).temporal_classification == "AT_ONSET"
    for value in ["2026-11-12T09:59:59Z", "2026-11-12T10:00:01Z"]:
        assert (
            classify_time(parse_timestamp(value), anchor, options).temporal_classification
            == "OUTSIDE_WINDOW"
        )


def test_offset_normalization_preserves_original_and_dst_instants():
    offset = parse_timestamp("2026-11-12T13:00:00+03:00")
    utc = parse_timestamp("2026-11-12T10:00:00Z")
    assert offset.original == "2026-11-12T13:00:00+03:00"
    assert offset.utc == utc.utc
    assert classify_time(offset, utc, InvestigationOptions()).temporal_classification == "AT_ONSET"
    # The repeated local DST hour names two different instants when offsets differ.
    assert parse_timestamp("2026-11-01T01:30:00-04:00").utc == "2026-11-01T05:30:00Z"
    assert parse_timestamp("2026-11-01T01:30:00-05:00").utc == "2026-11-01T06:30:00Z"


@pytest.mark.parametrize(
    "value",
    [
        "2026-11-12T10:00:00",
        "2026-11-12 10:00:00Z",
        "2026-11-12",
        "broken",
        "2026-11-12T10:00:00-00:00",
        "2026-11-12T10:00:00+00:60",
        "2026-11-12T10:00:00.123456789Z",
        "2026-02-30T10:00:00Z",
        123,
        True,
    ],
)
def test_invalid_timestamp_never_silently_assumes_utc(value):
    parsed = parse_timestamp(value)
    assert parsed.utc is None
    assert parsed.original == value
    assert parsed.warning_code == "INVALID_TIMESTAMP"
    assert (
        classify_time(
            parsed, parse_timestamp("2026-11-12T10:00:00Z"), InvestigationOptions()
        ).temporal_classification
        == "UNKNOWN"
    )


@pytest.mark.parametrize("value", [None, ""])
def test_missing_timestamp_is_distinct_from_invalid(value):
    assert parse_timestamp(value).warning_code == "MISSING_TIMESTAMP"


def test_explicit_semantic_timestamp_does_not_fall_back_to_ingestion():
    properties = {
        "incident_started_at": "invalid",
        "timestamp": "2026-11-12T10:00:00Z",
        "ingested_at": "2026-11-12T10:01:00Z",
    }
    parsed = entity_timestamp(properties, "incident_started_at")
    assert parsed.source_field == "incident_started_at"
    assert parsed.utc is None
    assert parsed.warning_code == "INVALID_TIMESTAMP"
    assert entity_timestamp({"ingested_at": properties["ingested_at"]}, "observed_at").utc is None


def test_extreme_datetime_window_does_not_overflow():
    anchor = parse_timestamp("0001-01-01T00:00:00Z")
    assert (
        classify_time(anchor, anchor, InvestigationOptions()).temporal_classification == "AT_ONSET"
    )


@pytest.mark.parametrize(
    "options",
    [
        {"pre_minutes": -1},
        {"post_minutes": 1441},
        {"pre_minutes": True},
        {"post_minutes": 2.5},
        {"max_candidates": 101},
        {"max_evidence": 0},
    ],
)
def test_options_reject_invalid_types_and_ranges(options):
    with pytest.raises(ValidationError):
        InvestigationOptions(**options)
