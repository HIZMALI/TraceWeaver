"""CONTROLLED timeout provider; actual immutable native judge graph. No Ollama HTTP request."""

import argparse
from pathlib import Path

import uvicorn

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.ollama_local import OllamaFailure, OllamaLocal


def controlled(self, method, route, payload=None, *, deadline=None):
    if (method, route) == ("GET", "/api/tags"):
        return {"models": [{"name": "controlled-recovery:1", "size": 1}]}
    raise OllamaFailure("OLLAMA_TIMEOUT")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Bounded numeric loopback port required")
    root = Path(__file__).resolve().parents[2]
    OllamaLocal._request = controlled
    uvicorn.run(
        create_app(Settings(database=root / "examples/judge-demo/traceweaver-demo.rl")),
        host="127.0.0.1",
        port=args.port,
        log_level="error",
    )
