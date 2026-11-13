"""Fixed-loopback native Ollama tools; no source prose, raw IDs, retries or model pulls."""

import time
from typing import Annotated

from pydantic import Field

from traceweaver.agent_models import ToolArguments
from traceweaver.agent_tools import HANDLERS
from traceweaver.model_selection import ModelProposal, valid_model_id
from traceweaver.ollama_local import OllamaFailure, OllamaLocal

ROUND_SECONDS = 20
TOTAL_SECONDS = 90


class AgentFinalProposal(ModelProposal):
    tool_steps: Annotated[list[Annotated[int, Field(ge=1, le=4)]], Field(max_length=4)] = []


class AgentProvider:
    def __init__(self, model, deadline):
        self.model, self.deadline = model, deadline
        self.client = OllamaLocal()
        self.interactions = 0
        self.diagnostics = None
        self.offered_claim_count = 0

    def request(self, method, route, payload=None):
        try:
            result = self.client._request(
                method,
                route,
                payload,
                deadline=min(self.deadline, time.monotonic() + ROUND_SECONDS),
            )
        except OllamaFailure as exc:
            if self.diagnostics is not None:
                self.diagnostics.failure("transport", exc.code)
            raise
        if not isinstance(result, dict):
            raise OllamaFailure("AGENT_RESPONSE_SCHEMA")
        return result

    def check_installed(self):
        if not valid_model_id(self.model):
            raise OllamaFailure("OLLAMA_MODEL_REQUIRED", unavailable=True)
        models = self.request("GET", "/api/tags").get("models")
        if not isinstance(models, list) or len(models) > 256:
            raise OllamaFailure("OLLAMA_TAGS_SCHEMA")
        if not any(
            isinstance(m, dict)
            and m.get("name") == self.model
            and type(m.get("size")) is int
            and m["size"] > 0
            and not any(k.startswith("remote_") for k in m)
            for m in models
        ):
            raise OllamaFailure("OLLAMA_MODEL_NOT_INSTALLED", unavailable=True)

    def chat(self, messages, tools, *, final=False):
        if self.interactions >= 5:
            raise OllamaFailure("AGENT_MODEL_BUDGET")
        self.interactions += 1
        body = {
            "model": self.model,
            "stream": False,
            "think": False,
            "messages": messages,
            "options": {"temperature": 0, "num_predict": 768, "num_ctx": 8192},
        }
        if tools and not final:
            body["tools"] = tools
        if final:
            body["format"] = AgentFinalProposal.model_json_schema()
        if self.diagnostics is not None:
            self.diagnostics.request(body, final=final, offered_count=self.offered_claim_count)
        response = self.request("POST", "/api/chat", body)
        if self.diagnostics is not None:
            self.diagnostics.response(response, final=final)
        message = response.get("message")
        if (
            response.get("done") is not True
            or response.get("model") != self.model
            or response.get("done_reason", "stop") != "stop"
            or not isinstance(message, dict)
            or message.get("role") != "assistant"
            or set(message) - {"role", "content", "thinking", "tool_calls"}
            or not isinstance(message.get("content"), str)
        ):
            raise OllamaFailure("AGENT_CHAT_SCHEMA")
        return message


def tool_definitions(context, used):
    result = []
    for name, (kind, _) in HANDLERS.items():
        subjects = [
            key for key, (k, _) in context.subjects.items() if k == kind and (name, key) not in used
        ]
        if subjects:
            schema = ToolArguments.model_json_schema()
            schema["properties"]["subject"]["enum"] = subjects
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": "Read bounded native context. Select one offered opaque "
                        "subject. No cause is established.",
                        "parameters": schema,
                    },
                }
            )
    return result
