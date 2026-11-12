from copy import deepcopy

import pytest
from pydantic import ValidationError

from traceweaver.citation_validator import CitationRejected, CitationValidator
from traceweaver.explanation_catalog import build_catalog, claim_id
from traceweaver.explanation_models import Claim


def validate_changed(context, catalog, data):
    changed = catalog.model_copy(deep=True)
    changed.claims[0] = Claim.model_validate(data)
    return CitationValidator(context, changed).validate(
        [data["claim_id"]], changed.investigation_fingerprint, require_caution=False
    )


def test_all_admitted_claims_have_semantic_support(scenario_context, scenario_catalog):
    validator = CitationValidator(scenario_context, scenario_catalog)
    for claim in scenario_catalog.claims:
        validated = validator.validate(
            [claim.claim_id], scenario_catalog.investigation_fingerprint, require_caution=False
        )
        assert validated == [claim]


@pytest.mark.parametrize(
    "attack", ["unknown", "duplicates", "excessive", "cross_snapshot", "no_caution"]
)
def test_selection_scope_and_limits_reject(scenario_context, scenario_catalog, attack):
    ids = [scenario_catalog.claims[0].claim_id]
    snapshot = scenario_catalog.investigation_fingerprint
    if attack == "unknown":
        ids = ["C-" + "0" * 24]
    if attack == "duplicates":
        ids *= 2
    if attack == "excessive":
        ids *= 11
    if attack == "cross_snapshot":
        snapshot = "0" * 64
    if attack == "no_caution":
        ids = [
            next(c.claim_id for c in scenario_catalog.claims if c.claim_type == "EVIDENCE_REPORTED")
        ]
    with pytest.raises(CitationRejected):
        CitationValidator(scenario_context, scenario_catalog).validate(ids, snapshot)


@pytest.mark.parametrize(
    "attack",
    [
        "direction",
        "path_order",
        "target",
        "timestamp",
        "temporal_class",
        "statement",
        "source_url",
        "provenance",
    ],
)
def test_semantic_tampering_rejected(scenario_context, scenario_catalog, attack):
    kind = (
        "EVIDENCE_REPORTED" if attack in {"source_url", "provenance"} else "DEPLOYMENT_BEFORE_ONSET"
    )
    data = deepcopy(next(c.model_dump() for c in scenario_catalog.claims if c.claim_type == kind))
    if attack == "statement":
        data["statement"] = "The deployment definitely caused this incident."
    if attack == "target":
        data["referenced_entity_ids"][1] = "CASE-UNRELATED"
        data["claim_id"] = claim_id(kind, data["referenced_entity_ids"])
    path = next(c for c in data["citations"] if c["graph_path"])
    if attack == "direction":
        path["graph_path"]["edges"][-1]["traversal_direction"] = "FORWARD"
    if attack == "path_order":
        path["graph_path"]["node_ids"].reverse()
    if attack in {"timestamp", "temporal_class"}:
        temporal = next(c for c in data["citations"] if c["kind"] == "TEMPORAL")
        temporal["event_utc" if attack == "timestamp" else "temporal_classification"] = (
            "2026-11-12T20:00:00Z" if attack == "timestamp" else "AFTER"
        )
    if attack in {"source_url", "provenance"}:
        provenance = next(c for c in data["citations"] if c["kind"] == "PROVENANCE")
        provenance["source_ref" if attack == "source_url" else "verification_status"] = (
            "https://invented.invalid" if attack == "source_url" else "UNVERIFIED_EXTERNAL"
        )
    with pytest.raises((CitationRejected, ValidationError)):
        validate_changed(scenario_context, scenario_catalog, data)


def test_cross_incident_evidence_id_and_real_path_cannot_be_reused(
    case_database, read_investigation, scenario_context, scenario_catalog
):
    other = build_catalog(read_investigation(case_database, "CASE-OTHER"))
    claim = next(c for c in other.claims if c.claim_type == "EVIDENCE_REPORTED")
    with pytest.raises(CitationRejected):
        validate_changed(scenario_context, scenario_catalog, claim.model_dump())


def test_undetermined_pair_cannot_be_relabelled_as_conflict(scenario_context, scenario_catalog):
    data = next(
        c.model_dump() for c in scenario_catalog.claims if c.claim_type == "COMPARISON_UNDETERMINED"
    )
    data["claim_type"] = "STRUCTURED_CONFLICT"
    data["claim_id"] = claim_id(data["claim_type"], data["referenced_entity_ids"])
    data["citations"][0]["classification"] = "CONFLICTING_OBSERVATIONS"
    with pytest.raises(CitationRejected):
        validate_changed(scenario_context, scenario_catalog, data)


def test_snapshot_copy_is_isolated_from_later_nested_mutation(scenario_context, scenario_catalog):
    validator = CitationValidator(scenario_context, scenario_catalog)
    snapshot = scenario_catalog.investigation_fingerprint
    identity = scenario_catalog.claims[0].claim_id
    scenario_context.incident["summary"] = "changed later"
    scenario_catalog.claims.clear()
    assert validator.validate([identity], snapshot)[0].claim_type == "NO_CAUSAL_VERDICT"
