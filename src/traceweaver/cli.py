"""Local commands. Only seed opens a writable connection."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from traceweaver.config import Settings
from traceweaver.queries import IncidentNotFound, incident_context
from traceweaver.seed import seed_database
from traceweaver.storage import GraphStore, StorageError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="traceweaver")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("seed", "stats", "context"):
        command = commands.add_parser(name)
        command.add_argument("--database", type=Path, default=None)
        if name == "seed":
            command.add_argument("--fixture", type=Path, default=None)
        if name == "context":
            command.add_argument("--incident", required=True)
    args = parser.parse_args(argv)
    try:
        config = Settings(database=args.database) if args.database is not None else Settings()
        if args.command == "seed":
            result = seed_database(config.database, args.fixture)
        else:
            with GraphStore(config.database) as store:
                result = (
                    store.counts()
                    if args.command == "stats"
                    else incident_context(store, args.incident).model_dump(mode="json")
                )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except IncidentNotFound:
        print("Incident not found", file=sys.stderr)
        return 3
    except (StorageError, OSError, ValueError, ValidationError) as exc:
        print(f"TraceWeaver error: {exc}", file=sys.stderr)
        return 1
