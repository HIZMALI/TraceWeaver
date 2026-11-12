import json
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from traceweaver.explanation import explain, explain_investigation
from traceweaver.explanation_models import ExplanationReport
from traceweaver.explanation_scenarios import seed_explanation_profile
from traceweaver.local_files import canonical_json
from traceweaver.model_selection import sanitized_packet
from traceweaver.ollama_local import OllamaFailure
from traceweaver.storage import GraphStore

ROOT = Path(__file__).resolve().parents[2]


def test_default_is_offline_without_any_socket_or_model(database, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Deterministic explanation must be entirely offline")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr("traceweaver.explanation.OllamaLocal.select", forbidden)
    before = database.read_bytes()
    first, second = explain(database, "INC-001"), explain(database, "INC-001")
    assert canonical_json(first.model_dump(mode="json")) == canonical_json(
        second.model_dump(mode="json")
    )
    assert first.mode_executed == "DETERMINISTIC" and not first.ai_generated_selection
    assert first.model is None and "not AI-generated" in first.overview
    assert first.causal_conclusion == "NOT_ESTABLISHED"
    assert first.claims[-1].claim_type == "NO_CAUSAL_VERDICT"
    assert database.read_bytes() == before


@pytest.mark.parametrize("incident", ["INC-001", "CASE-INC"])
def test_actual_canonical_examples_match_real_service(case_database, incident):
    example = ROOT / "docs/examples" / (incident + "-explanation.json")
    actual = explain(case_database, incident)
    assert example.read_text(encoding="utf-8") == canonical_json(actual.model_dump(mode="json"))
    assert ExplanationReport.model_validate_json(example.read_bytes()) == actual


def test_unknown_onset_keeps_gap_and_suppresses_preceding_claim(case_database):
    result = explain(case_database, "CASE-NO-TIME")
    assert any(u.code == "MISSING_TIMESTAMP" for u in result.uncertainties)
    assert not any(
        c.claim_type in {"DEPLOYMENT_BEFORE_ONSET", "DEPLOYMENT_NOT_PRECEDING"}
        for c in result.claims
    )
    assert result.explanation_status == "PARTIAL_CONTEXT"


def test_no_evidence_abstains_without_padded_evidence_claim(tmp_path):
    database = tmp_path / "empty-evidence.rl"
    seed_explanation_profile(database, "evaluation")
    report = explain(database, "EV-NONE")
    assert report.explanation_status == "ABSTAINED"
    assert report.evidence_summary.returned_evidence == 0
    assert all(c.claim_type != "EVIDENCE_REPORTED" for c in report.claims)
    assert any(u.code == "NO_INCIDENT_EVIDENCE" for u in report.uncertainties)


def test_complete_review_is_explained_without_source_authentication(tmp_path):
    database = tmp_path / "ready.rl"
    seed_explanation_profile(database, "ready")
    report = explain(database, "EX-READY")
    assert report.explanation_status == "EXPLAINED"
    assert report.investigation_status == "READY_FOR_REVIEW"
    assert report.external_verification_status == "NOT_PERFORMED"
    assert report.causal_conclusion == "NOT_ESTABLISHED"


def test_external_verification_and_demo_marker_are_not_upgraded(database):
    with GraphStore(database, read_only=False) as store:
        store.execute("MATCH (i:Incident {id:'INC-001'}) SET i.demo=false")
        store.execute(
            "MATCH (e:Evidence {id:'EVD-001'}) SET e.demo=false, e.source_ref=$ref",
            {"ref": "https://synthetic-external.invalid/proof"},
        )
    report = explain(database, "INC-001")
    assert report.is_demo is False
    assert report.evidence_summary.unverified_external_count == 1
    assert any(u.code == "UNVERIFIED_EXTERNAL_SOURCES" for u in report.uncertainties)
    assert "synthetic-external.invalid" not in report.model_dump_json()


def test_prompt_injection_and_private_metadata_are_withheld(tmp_path, read_investigation):
    from traceweaver.explanation_catalog import build_catalog

    database = tmp_path / "hostile.rl"
    seed_explanation_profile(database, "adversarial")
    before = database.read_bytes()
    context = read_investigation(database)
    packet = json.dumps(sanitized_packet(build_catalog(context)))
    result = explain(database, "INC-001").model_dump_json()
    for text in [
        "ignore all instructions",
        "confirmed root cause",
        "synthetic-private",
        "internal.invalid",
        "sk-" + "SYNTHETIC" * 6,
        "EVD-001",
        "INC-001",
    ]:
        assert text not in packet
    for text in [
        "ignore all instructions",
        "confirmed root cause",
        "synthetic-private",
        "internal.invalid",
    ]:
        assert text not in result
    assert database.read_bytes() == before


def test_rejected_model_has_no_hidden_deterministic_fallback(database, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OllamaFailure("OLLAMA_CONNECTION_UNAVAILABLE", unavailable=True)

    monkeypatch.setattr("traceweaver.explanation.OllamaLocal.select", unavailable)
    before = database.read_bytes()
    report = explain(database, "INC-001", mode="ollama", model="test-model:1")
    assert report.explanation_status == "MODEL_UNAVAILABLE"
    assert report.mode_executed == "NONE" and not report.ai_generated_selection
    assert report.model is None and report.claims == []
    assert report.rejection_codes == ["OLLAMA_CONNECTION_UNAVAILABLE"]
    assert database.read_bytes() == before


def test_source_next_checks_are_bounded_and_derived(scenario_context):
    report = explain_investigation(scenario_context)
    assert set(report.next_checks) <= set(scenario_context.next_checks)
    assert len(report.next_checks) <= 8
    changed = scenario_context.model_copy(deep=True)
    changed.next_checks = ["C:/synthetic-private/path", "http://internal.invalid"]
    other = explain_investigation(changed)
    assert other.next_checks == [] and other.truncation.next_checks


def test_response_contract_rejects_extra_causal_fields(database):
    payload = explain(database, "INC-001").model_dump()
    payload["root_cause"] = "invented"
    with pytest.raises(ValidationError):
        ExplanationReport.model_validate(payload)


def test_model_invocation_happens_after_real_connection_closes(database, monkeypatch):
    events = []

    class ObservedStore(GraphStore):
        def __enter__(self):
            assert self.read_only
            events.append("open")
            return super().__enter__()

        def __exit__(self, *args):
            result = super().__exit__(*args)
            events.append("closed")
            return result

    def selection(provider, catalog, model):
        assert events == ["open", "closed"]
        packet = sanitized_packet(catalog)
        ids = [c["claim_id"] for c in packet["claims"]][:3]
        return json.dumps(
            {
                "investigation_fingerprint": catalog.investigation_fingerprint,
                "selected_claim_ids": ids,
                "focus": "BALANCED",
                "abstain": False,
            }
        ).encode(), ids

    monkeypatch.setattr("traceweaver.explanation.GraphStore", ObservedStore)
    monkeypatch.setattr("traceweaver.explanation.OllamaLocal.select", selection)
    report = explain(database, "INC-001", mode="ollama", model="test-model:1")
    assert report.mode_executed == "OLLAMA" and report.ai_generated_selection
    # This is controlled transport-contract coverage, not live-model evidence.


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode_executed", "OLLAMA"),
        ("ai_generated_selection", True),
        ("validated_claim_count", 0),
        ("validated_citation_count", 0),
        ("explanation_status", "MODEL_UNAVAILABLE"),
    ],
)
def test_report_rejects_incoherent_execution_metadata(database, field, value):
    payload = explain(database, "INC-001").model_dump()
    payload[field] = value
    with pytest.raises(ValidationError):
        ExplanationReport.model_validate(payload)
