import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from traceweaver.ingestion import ingest
from traceweaver.investigation import investigate
from traceweaver.local_files import MAX_INPUT_BYTES, read_local_bytes
from traceweaver.source_integrity import verify_source
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "fixtures/ingestion_example.json"


def test_digest_match_mismatch_and_missing_expected_are_distinct(tmp_path):
    path = tmp_path / "exact-bytes.bin"
    path.write_bytes(b"\xff\x00synthetic\r\n")
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    for supplied, status in [
        (expected.upper(), "MATCH"),
        ("0" * 64, "MISMATCH"),
        (None, "NOT_CHECKED"),
    ]:
        result = verify_source(path, supplied)
        assert result.actual_sha256 == expected
        assert result.comparison_status == status
        assert result.byte_equality_established == (status == "MATCH")
        assert result.external_verification_status == "NOT_PERFORMED"
        assert "byte equality only" in result.warning


@pytest.mark.parametrize("expected", ["invalid", "g" * 64, "a" * 63, True])
def test_invalid_digest_has_safe_validation_error(expected):
    with pytest.raises(ToolError) as error:
        verify_source(EXAMPLE, expected)
    assert error.value.code == "INVALID_EXPECTED_DIGEST"


def test_mismatch_blocks_apply_before_parsing_and_writer_open(tmp_path):
    source = tmp_path / "not-even-json.json"
    source.write_bytes(b"DO_NOT_DISCLOSE_UNPARSED_BODY")
    database = tmp_path / "no-writer-directory" / "target.rl"
    with pytest.raises(ToolError) as error:
        ingest(source, database, apply=True, expected_sha256="0" * 64)
    assert error.value.code == "SOURCE_DIGEST_MISMATCH"
    assert error.value.as_dict()["integrity"]["comparison_status"] == "MISMATCH"
    assert "DO_NOT_DISCLOSE" not in json.dumps(error.value.as_dict())
    assert not database.parent.exists()


def test_embedded_checksum_is_not_an_independent_digest(tmp_path):
    data = json.loads(EXAMPLE.read_text())
    data["expected_sha256"] = "0" * 64
    source = tmp_path / "self-declared.json"
    source.write_text(json.dumps(data))
    assert verify_source(source).comparison_status == "NOT_CHECKED"
    with pytest.raises(ToolError, match="validation"):
        ingest(source, tmp_path / "absent.rl", apply=True)


@pytest.mark.parametrize(
    "path",
    [
        "https://example.invalid/input.json",
        "http://127.0.0.1/private",
        "file:///private/input.json",
        "\\\\server\\share\\input.json",
        "//server/share/input.json",
        "\\\\?\\C:\\input.json",
        "C:relative.json",
    ],
)
def test_network_device_and_ambiguous_paths_are_rejected_without_access(path):
    with pytest.raises(ToolError) as error:
        verify_source(path)
    assert error.value.code == "UNSAFE_LOCAL_PATH"


def test_symlink_or_junction_traversal_is_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "input.json").write_text("{}")
    link = tmp_path / "link"
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ToolError) as error:
        read_local_bytes(link / "input.json")
    assert error.value.code == "UNSAFE_LOCAL_PATH"


def test_regular_file_requirement_and_exact_byte_limit(tmp_path):
    with pytest.raises(ToolError) as error:
        verify_source(tmp_path)
    assert error.value.code == "NOT_REGULAR_FILE"
    path = tmp_path / "exact-limit.bin"
    path.write_bytes(b" " * MAX_INPUT_BYTES)
    assert verify_source(path).size_bytes == MAX_INPUT_BYTES


def test_external_reference_is_opaque_and_never_contacted(tmp_path, monkeypatch):
    def network_forbidden(*args, **kwargs):
        raise AssertionError("Outbound source access is forbidden")

    monkeypatch.setattr(socket, "getaddrinfo", network_forbidden)
    monkeypatch.setattr(socket.socket, "connect", network_forbidden)
    data = json.loads(EXAMPLE.read_text())
    for node in data["nodes"]:
        if node["label"] == "Evidence":
            node["properties"]["source_ref"] = "https://example.invalid/opaque-only"
    source = tmp_path / "opaque.json"
    source.write_text(json.dumps(data))
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    database = tmp_path / "offline.rl"
    result = ingest(source, database, apply=True, expected_sha256=expected)
    assert result["integrity"]["comparison_status"] == "MATCH"
    assert result["external_verification_status"] == "NOT_PERFORMED"
    with GraphStore(database) as store:
        review = investigate(store, "ING-INC-001")
    assert all(e.source_ref == "https://example.invalid/opaque-only" for e in review.evidence)
    assert all(e.provenance_status == "TRACEABLE" for e in review.evidence)
    assert review.causal_conclusion == "NOT_ESTABLISHED"


def test_verify_cli_does_not_depend_on_database_config_and_reports_mismatch(monkeypatch):
    monkeypatch.setenv("TRACEWEAVER_DATABASE", "invalid-not-a-store")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "verify-source",
            "--input",
            str(EXAMPLE),
            "--expected-sha256",
            "0" * 64,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 6
    assert json.loads(result.stdout)["comparison_status"] == "MISMATCH"
    assert json.loads(result.stdout)["external_verification_status"] == "NOT_PERFORMED"
    missing = subprocess.run(
        [
            sys.executable,
            "-m",
            "traceweaver",
            "verify-source",
            "--input",
            str(EXAMPLE.parent / "missing-never-created.json"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert missing.returncode == 9
    assert json.loads(missing.stderr)["error"]["code"] == "INPUT_NOT_FOUND"
    assert "Traceback" not in missing.stderr
