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
    "--profile",
    choices=(
        "judge",
        "missing",
        "adversarial",
        "empty",
        "caps",
        "perf-small",
        "perf-medium",
        "perf-capped",
    ),
    default="judge",
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
    if args.profile.startswith("perf-"):
        count = {"perf-small": 4, "perf-medium": 30, "perf-capped": 110}[args.profile]
        assert not database.exists()
        with GraphStore(database, read_only=False) as store:
            with store.transaction():
                store.execute(
                    "CREATE (i:Incident {id:$id, demo:true, title:$title, timestamp:$time})"
                    "-[:AFFECTS {demo:true}]->(:Service {id:$service, demo:true, name:$name})",
                    {
                        "id": "PERF-INC",
                        "title": "Synthetic browser scale specimen",
                        "time": "2026-11-12T10:00:00Z",
                        "service": "PERF-SVC",
                        "name": "Synthetic service",
                    },
                )
                for n in range(count):
                    store.execute(
                        "MATCH (i:Incident {id:$incident}), (s:Service {id:$service}) "
                        "CREATE (d:Deployment {id:$dep, demo:true, timestamp:$before})"
                        "-[:TARGETS {demo:true}]->(s), "
                        "(d)-[:INCLUDES_CHANGE {demo:true}]->(:Change {id:$change, demo:true}), "
                        "(i)-[:HAS_EVIDENCE {demo:true}]->(e:Evidence {id:$evidence, demo:true, "
                        "timestamp:$time, source:$source, source_ref:$reference, "
                        "signal_key:$signal, observed_state:$state, service_id:$service, "
                        "environment:$environment})"
                        "-[:OBSERVED_ON {demo:true}]->(s)",
                        {
                            "incident": "PERF-INC",
                            "service": "PERF-SVC",
                            "dep": f"PERF-D{n:03}",
                            "change": f"PERF-C{n:03}",
                            "evidence": f"PERF-E{n:03}",
                            "before": "2026-11-12T09:30:00Z",
                            "time": "2026-11-12T10:00:00Z",
                            "source": "synthetic-perf",
                            "reference": "demo://performance",
                            "signal": "availability",
                            "state": "HEALTHY",
                            "environment": "demo",
                        },
                    )
    uvicorn.run(
        create_app(Settings(database=database)),
        host="127.0.0.1",
        port=args.port,
        log_level="error",
        timeout_keep_alive=3,
    )
