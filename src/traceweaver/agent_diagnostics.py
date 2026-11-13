"""Opt-in structural metadata only. Nothing here changes agent admission or exposes prose."""

import http.client
import json
import re
import time
from datetime import UTC, datetime

from traceweaver.local_files import parse_json_document
from traceweaver.ollama_local import _DeadlineSocket
from traceweaver.tool_errors import ToolError

PROBE_MODEL = "qwen3:8b"


def _kind(value):
    return (
        "NULL"
        if value is None
        else "BOOLEAN"
        if type(value) is bool
        else "STRING"
        if isinstance(value, str)
        else "ARRAY"
        if isinstance(value, list)
        else "OBJECT"
        if isinstance(value, dict)
        else "NUMBER"
        if type(value) in (int, float)
        else "OTHER"
    )


class StructuralDiagnostics:
    """Explicit internal opt-in, bounded metadata export. Never an API response or logger."""

    def __init__(self):
        self._events = []
        self._dropped = 0
        self._snapshot = {}

    def _add(self, event):
        if len(self._events) >= 40 or len(json.dumps(event, ensure_ascii=True).encode()) > 4096:
            self._dropped += 1
        else:
            self._events.append(event)

    def bind(self, fingerprint, database_digest):
        if not all(re.fullmatch(r"[a-f0-9]{64}", s) for s in (fingerprint, database_digest)):
            raise ValueError("Diagnostic digest required")
        self._snapshot = {"source_fingerprint": fingerprint, "database_digest": database_digest}

    def request(self, body, *, final, offered_count):
        roles = [m.get("role") for m in body["messages"]]
        self._add(
            dict(
                phase="final_request" if final else "tool_request",
                tools_present=bool(body.get("tools")),
                format_kind="JSON_SCHEMA" if isinstance(body.get("format"), dict) else "NONE",
                stream=body.get("stream") is True,
                think=body.get("think") is True,
                history_roles=[
                    r if r in {"system", "user", "assistant", "tool"} else "OTHER"
                    for r in roles[-12:]
                ],
                history_truncated=len(roles) > 12,
                offered_claim_count=min(128, max(0, offered_count)),
            )
        )

    def response(self, value, *, final):
        message = value.get("message")
        message = message if isinstance(message, dict) else {}
        content = message.get("content")
        try:
            size = len(content.encode()) if isinstance(content, str) else None
        except UnicodeError:
            size = None
        reason = value.get("done_reason")
        calls = message.get("tool_calls")
        item = dict(
            phase="final_response" if final else "tool_response",
            message_present=isinstance(value.get("message"), dict),
            tool_calls_count=min(len(calls), 999) if isinstance(calls, list) else None,
            content_present=isinstance(content, str),
            content_size_bytes=size,
            done_reason=reason
            if reason is None
            or isinstance(reason, str)
            and reason in {"stop", "length", "load", "unload"}
            else "OTHER",
        )
        for field in ("eval_count", "prompt_eval_count"):
            n = value.get(field)
            item[field] = n if type(n) is int and 0 <= n <= 10**9 else None
        self._add(item)

    def finish(self, content, model):
        from pydantic import ValidationError

        item = dict(phase="final_schema", json_parse="NOT_PARSED", root_type="OTHER")
        if not isinstance(content, str):
            item["root_type"] = _kind(content)
            self._add(item)
            return
        try:
            if len(content.encode()) > 4096:
                self.failure("final_schema", "AGENT_FINISH_LIMIT")
                return
            # Bounded metadata inspection only. Admission still uses the duplicate/depth-safe
            # strict parser, independently. No parsed value is exported or used to repair output.
            value = json.loads(content)
            item.update(json_parse="PARSED", root_type=_kind(value))
            try:
                parse_json_document(content.encode(), max_depth=4)
                item["strict_object_parse"] = "ACCEPTED"
            except ToolError as exc:
                item["strict_object_parse"] = "REJECTED"
                item["strict_parse_code"] = exc.code
                self._add(item)
                return
            if isinstance(value, dict):
                known = set(model.model_fields)
                item["known_fields"] = {k: _kind(value[k]) for k in known if k in value}
                item["unknown_field_count"] = len(set(value) - known)
                selected = value.get("selected_claim_ids")
                item["selected_count"] = (
                    min(len(selected), 999) if isinstance(selected, list) else None
                )
            try:
                model.model_validate(value)
                item["schema_valid"] = True
            except ValidationError as exc:
                item["schema_valid"] = False
                types = {
                    "missing",
                    "extra_forbidden",
                    "string_type",
                    "string_pattern_mismatch",
                    "list_type",
                    "too_long",
                    "value_error",
                    "literal_error",
                    "bool_type",
                    "model_type",
                    "int_type",
                    "greater_than_equal",
                    "less_than_equal",
                }
                item["errors"] = [
                    {
                        "path": [
                            p
                            if isinstance(p, str) and p in model.model_fields
                            else p
                            if type(p) is int and 0 <= p <= 8
                            else "OTHER"
                            for p in e["loc"][:3]
                        ],
                        "type": e["type"] if e["type"] in types else "OTHER",
                    }
                    for e in exc.errors(
                        include_input=False, include_context=False, include_url=False
                    )[:8]
                ]
        except (ValueError, RecursionError, UnicodeError):
            item["json_parse"] = "REJECTED"
        self._add(item)

    def failure(self, phase, code):
        allowed = {"transport", "final_schema", "firewall", "tool_response", "final_response"}
        self._add(
            dict(
                phase=phase if phase in allowed else "OTHER",
                code=code if re.fullmatch(r"[A-Z_]{1,64}", code) else "OTHER",
                support_check="REJECTED",
            )
        )

    def admitted(self, selected_count):
        self._add(dict(phase="firewall", support_check="ADMITTED", selected_count=selected_count))

    def export(self):
        result = {
            "diagnostic_version": "1.0",
            "snapshot": self._snapshot,
            "events": self._events,
            "events_dropped": self._dropped,
        }
        # The sink is transient and not enabled for HTTP. Never silently emit an unbounded file.
        if len(json.dumps(result, ensure_ascii=True).encode()) > 32768:
            raise ValueError("Diagnostic metadata limit")
        return json.loads(json.dumps(result, ensure_ascii=True))


def _probe_get(route):
    if route not in {"/api/version", "/api/tags"}:
        raise ToolError("DIAGNOSTIC_ROUTE_REJECTED", "Fixed read-only probe routes only.")
    connection = http.client.HTTPConnection("127.0.0.1", 11434, timeout=2)
    deadline = time.monotonic() + 3
    try:
        connection.connect()
        connection.sock = _DeadlineSocket(connection.sock, deadline)
        connection.request("GET", route)
        response = connection.getresponse()
        if response.status != 200:
            return None, "HTTP_STATUS"
        if response.getheader("Content-Type", "").split(";")[0].strip() != "application/json":
            return None, "RESPONSE_TYPE"
        length = response.getheader("Content-Length")
        if length is not None and (not length.isdigit() or int(length) > 65536):
            return None, "RESPONSE_LIMIT"
        raw = response.read(65537)
        if len(raw) > 65536:
            return None, "RESPONSE_LIMIT"
        try:
            value = parse_json_document(raw, max_depth=8)
        except ToolError:
            return None, "RESPONSE_JSON"
        return (value, None) if isinstance(value, dict) else (None, "RESPONSE_ROOT")
    except ConnectionRefusedError:
        return None, "CONNECTION_REFUSED"
    except TimeoutError:
        return None, "TIMEOUT"
    except (OSError, http.client.HTTPException):
        return None, "CONNECTION_UNAVAILABLE"
    finally:
        connection.close()


def probe_local_ollama():
    """One version request then, only on valid success, one tags request. No retry or inference."""
    started = time.monotonic()
    result = dict(
        phase="connect",
        probed_at=datetime.now(UTC).isoformat(),
        request_count=1,
        reachable=False,
        daemon_version=None,
        requested_model=PROBE_MODEL,
        eligible_model_installed=None,
        model_capabilities="NOT_QUERIED",
        live_gate="BLOCKED_DEPENDENCY",
        failure_class=None,
    )
    version, failure = _probe_get("/api/version")
    result["failure_class"] = failure
    result["reachable"] = failure in {
        "HTTP_STATUS",
        "RESPONSE_TYPE",
        "RESPONSE_LIMIT",
        "RESPONSE_JSON",
        "RESPONSE_ROOT",
    }
    if version is not None:
        result["reachable"] = True
        name = version.get("version")
        if not isinstance(name, str) or not re.fullmatch(
            r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?:[-+][A-Za-z0-9.-]{1,32})?", name
        ):
            result["failure_class"] = "VERSION_SCHEMA"
        else:
            result["daemon_version"] = name
            result["request_count"] = 2
            tags, failure = _probe_get("/api/tags")
            result["failure_class"] = failure
            if tags is not None:
                models = tags.get("models")
                if not isinstance(models, list) or len(models) > 256:
                    result["failure_class"] = "TAGS_SCHEMA"
                else:
                    eligible = any(
                        isinstance(m, dict)
                        and m.get("name") == PROBE_MODEL
                        and type(m.get("size")) is int
                        and m["size"] > 0
                        and not any(k.startswith("remote_") for k in m)
                        for m in models
                    )
                    result["eligible_model_installed"] = eligible
                    result["live_gate"] = (
                        "AVAILABLE_FOR_EXPLICIT_TRIAL" if eligible else "BLOCKED_DEPENDENCY"
                    )
                    if not eligible:
                        result["failure_class"] = "MODEL_NOT_INSTALLED"
    result["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
    return result
