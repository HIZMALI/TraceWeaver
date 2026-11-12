"""Local commands. Only seed opens a writable connection."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from traceweaver.config import Settings
from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.queries import IncidentNotFound, incident_context
from traceweaver.seed import seed_database
from traceweaver.storage import GraphStore, StorageError
from traceweaver.temporal import integer_query


def bounded_integer(minimum: int, maximum: int):
    def parse(value: str) -> int:
        try:
            number = integer_query(value)
        except ValueError:
            raise argparse.ArgumentTypeError("Expected an integer") from None
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"Value must be between {minimum} and {maximum}")
        return number

    return parse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="traceweaver")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("seed", "stats", "context", "investigate"):
        command = commands.add_parser(name)
        command.add_argument("--database", type=Path, default=None)
        if name == "seed":
            command.add_argument("--fixture", type=Path, default=None)
        if name in ("context", "investigate"):
            command.add_argument("--incident", required=True)
        if name == "investigate":
            command.add_argument("--pre-minutes", type=bounded_integer(0, 1440), default=120)
            command.add_argument("--post-minutes", type=bounded_integer(0, 1440), default=30)
            command.add_argument("--max-candidates", type=bounded_integer(1, 100), default=100)
            command.add_argument("--max-evidence", type=bounded_integer(1, 100), default=100)
    args = parser.parse_args(argv)
    try:
        config = Settings(database=args.database) if args.database is not None else Settings()
        if args.command == "seed":
            result = seed_database(config.database, args.fixture)
        else:
            with GraphStore(config.database) as store:
                if args.command == "investigate":
                    options = InvestigationOptions(
                        pre_minutes=args.pre_minutes,
                        post_minutes=args.post_minutes,
                        max_candidates=args.max_candidates,
                        max_evidence=args.max_evidence,
                    )
                    result = investigate(store, args.incident, options).model_dump(mode="json")
                else:
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
