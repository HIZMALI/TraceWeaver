"""Offline byte equality, deliberately independent of provenance and source truth."""

import hashlib
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from traceweaver.local_files import read_local_bytes
from traceweaver.tool_errors import ToolError


class SourceIntegrity(BaseModel):
    integrity_contract_version: Literal["1.0"] = "1.0"
    algorithm: Literal["SHA-256"] = "SHA-256"
    size_bytes: int
    actual_sha256: str
    expected_sha256: str | None
    comparison_status: Literal["MATCH", "MISMATCH", "NOT_CHECKED"]
    byte_equality_established: bool
    external_verification_status: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    warning: str = (
        "A matching operator-supplied digest establishes byte equality only, not source "
        "authenticity or factual truth. External references are never contacted."
    )


def inspect_bytes(data: bytes, expected_sha256: str | None = None) -> SourceIntegrity:
    if expected_sha256 is not None and (
        not isinstance(expected_sha256, str)
        or not re.fullmatch(r"[0-9A-Fa-f]{64}", expected_sha256)
    ):
        raise ToolError(
            "INVALID_EXPECTED_DIGEST", "Expected SHA-256 must contain exactly 64 hex characters."
        )
    actual = hashlib.sha256(data).hexdigest()
    expected = expected_sha256.lower() if expected_sha256 is not None else None
    comparison = (
        "NOT_CHECKED" if expected is None else "MATCH" if actual == expected else "MISMATCH"
    )
    return SourceIntegrity(
        size_bytes=len(data),
        actual_sha256=actual,
        expected_sha256=expected,
        comparison_status=comparison,
        byte_equality_established=comparison == "MATCH",
    )


def verify_source(path: str | Path, expected_sha256: str | None = None) -> SourceIntegrity:
    return inspect_bytes(read_local_bytes(path), expected_sha256)
