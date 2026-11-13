"""Explicit local actions reuse the established opaque-ID selection firewall."""

import asyncio
import hmac
from typing import Annotated, Literal

from fastapi import HTTPException, Request
from pydantic import Field, ValidationError, field_validator

from traceweaver.dashboard import PRIVATE, read_entity_kinds
from traceweaver.explanation import explain_investigation
from traceweaver.explanation_catalog import fingerprint
from traceweaver.explanation_models import Digest, ExplanationReport, StrictModel
from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.local_files import parse_json_document
from traceweaver.model_selection import valid_model_id
from traceweaver.ollama_local import OllamaFailure, OllamaLocal
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError


class CapabilityRequest(StrictModel):
    action: Literal["LIST_INSTALLED_MODELS"]


class CapabilityResult(StrictModel):
    models: Annotated[list[str], Field(max_length=32)]
    truncated: bool = False
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    code: str | None = None


class SelectionRequest(StrictModel):
    incident_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")]
    options: InvestigationOptions
    source_fingerprint: Digest
    model_id: Annotated[str, Field(min_length=1, max_length=128)]
    confirmed: Literal[True]

    @field_validator("model_id")
    @classmethod
    def model_local(cls, value):
        if not valid_model_id(value) or PRIVATE.search(value):
            raise ValueError("Invalid local model ID")
        return value

    @field_validator("confirmed", mode="before")
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError("Confirmation is required")
        return value


class SelectionResult(StrictModel):
    source_fingerprint: Digest
    explanation: ExplanationReport


def action_contract(schema):
    """Document the same strict model used after bounded parsing, without eager body parsing."""
    document = schema.model_json_schema()
    definitions = document.pop("$defs", {})

    def inline(value):
        if isinstance(value, list):
            return [inline(item) for item in value]
        if isinstance(value, dict):
            if "$ref" in value:
                return inline(definitions[value["$ref"].removeprefix("#/$defs/")])
            return {key: inline(item) for key, item in value.items()}
        return value

    return {
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": inline(document)}},
        }
    }


async def bounded_action(request: Request, schema):
    types = request.headers.getlist("content-type")
    lengths = request.headers.getlist("content-length")
    if types != ["application/json"] or request.headers.get("content-encoding"):
        raise HTTPException(415, "Bounded application/json required")
    if len(lengths) > 1 or (
        lengths and (len(lengths[0]) > 4 or not lengths[0].isdigit() or int(lengths[0]) > 2048)
    ):
        raise HTTPException(413, "Console action exceeds size limit")

    async def read():
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 2048:
                raise HTTPException(413, "Console action exceeds size limit")
        return bytes(body)

    try:
        raw = await asyncio.wait_for(read(), timeout=2)
        return schema.model_validate(parse_json_document(raw, max_depth=4))
    except TimeoutError:
        raise HTTPException(408, "Console action body timeout") from None
    except (ToolError, ValidationError):
        raise HTTPException(422, "Invalid console action") from None


def installed_models():
    try:
        models = OllamaLocal()._request("GET", "/api/tags").get("models")
        if not isinstance(models, list) or len(models) > 256:
            raise OllamaFailure("OLLAMA_TAGS_SCHEMA")
        safe = sorted(
            {
                e["name"]
                for e in models
                if isinstance(e, dict)
                and valid_model_id(e.get("name"))
                and not PRIVATE.search(e["name"])
                and type(e.get("size")) is int
                and e["size"] > 0
                and not any(k.startswith("remote_") for k in e)
            }
        )
        return CapabilityResult(models=safe[:32], truncated=len(safe) > 32, status="AVAILABLE")
    except OllamaFailure as exc:
        return CapabilityResult(models=[], status="UNAVAILABLE", code=exc.code)


def select_local(database, action):
    with GraphStore(database) as store:
        source = investigate(store, action.incident_id, action.options)
        read_entity_kinds(store, source)
    digest = fingerprint(source)
    if not hmac.compare_digest(digest, action.source_fingerprint):
        raise HTTPException(409, "Context changed; refresh before local selection")
    # Native reader is closed; the existing adapter checks tags again and sends opaque IDs only.
    report = explain_investigation(source, mode="ollama", model=action.model_id)
    if report.investigation_fingerprint != digest:
        raise ToolError("CONSOLE_SELECTION_SNAPSHOT", "Selection snapshot cannot be verified.")
    return SelectionResult(source_fingerprint=digest, explanation=report)
