"""Read-only, single-origin judge launcher usable from a non-editable wheel."""

import argparse
import hashlib
import json
from importlib.resources import files
from pathlib import Path

import uvicorn

from traceweaver.api import create_app
from traceweaver.config import Settings
from traceweaver.dashboard import dashboard
from traceweaver.judge_demo import ARTIFACT_NAME, verify_judge_demo
from traceweaver.storage import StorageError
from traceweaver.tool_errors import ToolError


def check_bundle(bundle):
    directory = Path(bundle)
    path = directory / ARTIFACT_NAME
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = verify_judge_demo(directory)
    assets = files("traceweaver").joinpath("web_static")
    if not assets.joinpath("index.html").is_file() or not any(
        item.name.endswith(".js") for item in assets.joinpath("assets").iterdir()
    ):
        raise ToolError(
            "CONSOLE_BUILD_REQUIRED", "Build web assets before launching the judge console."
        )
    reports = [dashboard(path, identity) for identity in ("INC-001", "CASE-INC")]
    if hashlib.sha256(path.read_bytes()).hexdigest() != before:
        raise ToolError("JUDGE_STORE_CHANGED", "Judge store bytes changed during verification.")
    return {
        "status": "PASS",
        "read_only": True,
        "database_engine": "relate",
        "artifact_sha256": before,
        "graph_counts": manifest["graph_counts"],
        "built_console": True,
        "incidents": [
            {
                "id": b.investigation.incident_id,
                "candidates": len(b.investigation.candidates),
                "evidence": len(b.investigation.evidence),
                "causal_conclusion": b.explanation.causal_conclusion,
            }
            for b in reports
        ],
        "model_invoked": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only TraceWeaver synthetic judge console")
    parser.add_argument(
        "--bundle", required=True, help="Existing intact synthetic judge bundle directory"
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify data, built assets and native snapshots, then exit",
    )
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535")
    try:
        result = check_bundle(args.bundle)
    except (ToolError, StorageError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "detail": "Judge bundle or console build unavailable; see setup instructions.",
                }
            )
        )
        return 1
    if args.check:
        print(json.dumps(result, sort_keys=True))
        return 0
    print(f"Open http://127.0.0.1:{args.port}/?incident=INC-001 (Ctrl+C to stop)")
    uvicorn.run(
        create_app(Settings(database=Path(args.bundle) / ARTIFACT_NAME)),
        host="127.0.0.1",
        port=args.port,
        proxy_headers=False,
        workers=1,
        timeout_keep_alive=3,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
