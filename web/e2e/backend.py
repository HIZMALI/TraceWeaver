"""Owned finite browser-test server. Writes only newly allocated temporary synthetic stores."""

import argparse
import tempfile
from pathlib import Path

import uvicorn

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.explanation_scenarios import seed_explanation_profile
from traceweaver.storage import GraphStore

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, required=True)
parser.add_argument(
    "--profile", choices=("judge", "missing", "adversarial", "empty", "caps"), default="judge"
)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="traceweaver-browser-") as temporary:
    database = (
        root / "examples/judge-demo/traceweaver-demo.rl"
        if args.profile == "judge"
        else Path(temporary) / "case.rl"
    )
    if args.profile in {"adversarial", "empty", "caps"}:
        seed_explanation_profile(
            database,
            {"adversarial": "adversarial", "empty": "evaluation", "caps": "caps"}[args.profile],
        )
        if args.profile == "adversarial":
            with GraphStore(database, read_only=False) as store:
                store.execute(
                    "MATCH (i:Incident {id:$id}) SET i.title=$title",
                    {"id": "INC-001", "title": "<img src=x onerror=window.__injected=true>"},
                )
    uvicorn.run(
        create_app(Settings(database=database)),
        host="127.0.0.1",
        port=args.port,
        log_level="error",
        timeout_keep_alive=3,
    )
