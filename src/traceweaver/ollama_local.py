"""Optional bounded native Ollama calls to one fixed trusted loopback service."""

import http.client
import io
import json
import time

from traceweaver.model_selection import ModelProposal, sanitized_packet, valid_model_id
from traceweaver.tool_errors import ToolError

HOST = "127.0.0.1"
PORT = 11434
CONNECT_TIMEOUT = 2
READ_TIMEOUT = 30
TOTAL_TIMEOUT = 45
MAX_RESPONSE_BYTES = 65536
MAX_REQUEST_BYTES = 49152


class OllamaFailure(ToolError):
    def __init__(self, code, *, unavailable=False):
        super().__init__(
            code,
            "Local Ollama selection failed; no model prose is disclosed.",
            12 if unavailable else 13,
        )
        self.unavailable = unavailable


class _DeadlineReader(io.RawIOBase):
    def __init__(self, sock, deadline):
        self._socket = sock
        self._stream = sock.makefile("rb", buffering=0)
        self._deadline = deadline

    def readable(self):
        return True

    def readinto(self, buffer):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        self._socket.settimeout(min(READ_TIMEOUT, remaining))
        return self._stream.readinto(buffer)

    def close(self):
        self._stream.close()
        super().close()


class _DeadlineSocket:
    def __init__(self, sock, deadline):
        self._socket, self._deadline = sock, deadline

    def __getattr__(self, name):
        return getattr(self._socket, name)

    def makefile(self, *args, **kwargs):
        return io.BufferedReader(_DeadlineReader(self._socket, self._deadline))


class OllamaLocal:
    def _request(self, method: str, route: str, payload=None, *, deadline=None) -> dict:
        if (method, route) not in {("GET", "/api/tags"), ("POST", "/api/chat")}:
            raise OllamaFailure("OLLAMA_ROUTE_REJECTED")
        body = (
            None
            if payload is None
            else json.dumps(payload, ensure_ascii=True, allow_nan=False).encode()
        )
        if body is not None and len(body) > MAX_REQUEST_BYTES:
            raise OllamaFailure("OLLAMA_REQUEST_LIMIT")
        remaining = (
            TOTAL_TIMEOUT if deadline is None else min(TOTAL_TIMEOUT, deadline - time.monotonic())
        )
        if remaining <= 0:
            raise OllamaFailure("OLLAMA_TIMEOUT")
        connection = http.client.HTTPConnection(HOST, PORT, timeout=min(CONNECT_TIMEOUT, remaining))
        deadline = time.monotonic() + remaining
        try:
            try:
                connection.connect()
            except TimeoutError:
                raise OllamaFailure("OLLAMA_CONNECTION_UNAVAILABLE", unavailable=True) from None
            connection.sock.settimeout(min(READ_TIMEOUT, max(0.001, deadline - time.monotonic())))
            connection.sock = _DeadlineSocket(connection.sock, deadline)
            connection.request(
                method, route, body=body, headers={"Content-Type": "application/json"}
            )
            response = connection.getresponse()
            if response.status != 200:
                raise OllamaFailure("OLLAMA_HTTP_STATUS", unavailable=response.status == 404)
            if response.getheader("Content-Type", "").split(";")[0].strip() != "application/json":
                raise OllamaFailure("OLLAMA_RESPONSE_TYPE")
            length = response.getheader("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_RESPONSE_BYTES):
                raise OllamaFailure("OLLAMA_RESPONSE_LIMIT")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise OllamaFailure("OLLAMA_RESPONSE_LIMIT")
            from traceweaver.local_files import parse_json_document

            try:
                return parse_json_document(raw, max_depth=8)
            except ToolError:
                raise OllamaFailure("OLLAMA_RESPONSE_JSON") from None
        except TimeoutError:
            raise OllamaFailure("OLLAMA_TIMEOUT") from None
        except (OSError, http.client.HTTPException):
            raise OllamaFailure("OLLAMA_CONNECTION_UNAVAILABLE", unavailable=True) from None
        finally:
            connection.close()

    def select(self, catalog, model_id: str):
        if not valid_model_id(model_id):
            raise OllamaFailure("OLLAMA_MODEL_REQUIRED", unavailable=True)
        tags = self._request("GET", "/api/tags")
        models = tags.get("models")
        if not isinstance(models, list) or len(models) > 256:
            raise OllamaFailure("OLLAMA_TAGS_SCHEMA")
        installed = next(
            (
                entry
                for entry in models
                if isinstance(entry, dict) and entry.get("name") == model_id
            ),
            None,
        )
        if (
            installed is None
            or type(installed.get("size")) is not int
            or installed["size"] <= 0
            or any(key.startswith("remote_") for key in installed)
        ):
            raise OllamaFailure("OLLAMA_MODEL_NOT_INSTALLED", unavailable=True)
        packet = sanitized_packet(catalog)
        request = {
            "model": model_id,
            "stream": False,
            "think": False,
            "messages": [
                {
                    "role": "system",
                    "content": "You select existing claim IDs only. Return exactly "
                    "the required JSON schema. Copy investigation_fingerprint. Do not write facts, "
                    "citations, explanations, tools or additional fields. "
                    "Prefer a balanced selection.",
                },
                {
                    "role": "user",
                    "content": json.dumps(packet, ensure_ascii=True, separators=(",", ":")),
                },
            ],
            "format": ModelProposal.model_json_schema(),
            "options": {"temperature": 0, "num_predict": 512, "num_ctx": 8192},
        }
        response = self._request("POST", "/api/chat", request)
        message = response.get("message")
        if (
            response.get("done") is not True
            or response.get("model") != model_id
            or response.get("done_reason", "stop") != "stop"
            or not isinstance(message, dict)
            or message.get("role") != "assistant"
            or set(message) - {"role", "content", "thinking"}
            or not isinstance(message.get("content"), str)
        ):
            raise OllamaFailure("OLLAMA_CHAT_SCHEMA")
        try:
            raw = message["content"].encode("utf-8")
        except UnicodeError:
            raise OllamaFailure("OLLAMA_CHAT_SCHEMA") from None
        return raw, [c["claim_id"] for c in packet["claims"]]
