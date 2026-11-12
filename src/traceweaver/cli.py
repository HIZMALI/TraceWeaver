"""Local commands with explicit writers and separate offline-tool error contracts."""

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
from traceweaver.tool_errors import ToolError


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


def offline_command(args) -> int:
    # Keep new tooling errors separate from legacy CLI diagnostics and response contracts.
    from traceweaver.evaluation import evaluate_to_files
    from traceweaver.ingestion import ingest
    from traceweaver.judge_demo import build_judge_demo
    from traceweaver.source_integrity import verify_source

    try:
        exit_code = 0
        if args.command == "ingest":
            result = ingest(
                args.input,
                args.database,
                apply=args.apply,
                allow_non_demo=args.allow_non_demo,
                expected_sha256=args.expected_sha256,
            )
        elif args.command == "verify-source":
            result = verify_source(args.input, args.expected_sha256).model_dump()
            exit_code = 6 if result["comparison_status"] == "MISMATCH" else 0
        elif args.command == "evaluate":
            result = evaluate_to_files(args.suite, args.output, overwrite=args.overwrite)
            exit_code = 11 if result["failed"] else 0
        else:
            result = build_judge_demo(args.output_dir, force=args.force)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False))
        return exit_code
    except ToolError as exc:
        print(json.dumps(exc.as_dict(), sort_keys=True), file=sys.stderr)
        return exc.exit_code
    except (OSError, StorageError, ValueError):
        print(
            json.dumps(
                {
                    "committed": None,
                    "error": {
                        "code": "TOOL_OPERATION_ERROR",
                        "message": "Offline operation failed; internal details are not disclosed.",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="traceweaver")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("seed", "stats", "context", "investigate", "explain"):
        command = commands.add_parser(name)
        command.add_argument("--database", type=Path, default=None)
        if name == "seed":
            command.add_argument("--fixture", type=Path, default=None)
        if name in ("context", "investigate", "explain"):
            command.add_argument("--incident", required=True)
        if name in ("investigate", "explain"):
            command.add_argument("--pre-minutes", type=bounded_integer(0, 1440), default=120)
            command.add_argument("--post-minutes", type=bounded_integer(0, 1440), default=30)
            command.add_argument("--max-candidates", type=bounded_integer(1, 100), default=100)
            command.add_argument("--max-evidence", type=bounded_integer(1, 100), default=100)
        if name == "explain":
            command.add_argument(
                "--mode", choices=("deterministic", "ollama"), default="deterministic"
            )
            command.add_argument("--model")
    command = commands.add_parser("ingest")
    command.add_argument("--input", required=True)
    command.add_argument("--database", required=True)
    command.add_argument("--apply", action="store_true")
    command.add_argument("--allow-non-demo", action="store_true")
    command.add_argument("--expected-sha256")
    command = commands.add_parser("verify-source")
    command.add_argument("--input", required=True)
    command.add_argument("--expected-sha256")
    command = commands.add_parser("evaluate")
    command.add_argument("--suite", required=True)
    command.add_argument("--output", required=True)
    command.add_argument("--overwrite", action="store_true")
    command = commands.add_parser("build-judge-demo")
    command.add_argument("--output-dir", required=True)
    command.add_argument("--force", action="store_true")
    command = commands.add_parser("evaluate-explanations")
    command.add_argument("--suite", required=True)
    command.add_argument("--output", required=True)
    command.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.command in {"explain", "evaluate-explanations"}:
        return explanation_command(args)
    if args.command in {"ingest", "verify-source", "evaluate", "build-judge-demo"}:
        return offline_command(args)
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


def explanation_command(args) -> int:
    from traceweaver.explanation import explain

    try:
        if args.command == "evaluate-explanations":
            from traceweaver.explanation_evaluation import evaluate_explanations

            result = evaluate_explanations(args.suite, args.output, overwrite=args.overwrite)
            code = 14 if result["failed"] else 0
        else:
            config = Settings(database=args.database) if args.database is not None else Settings()
            options = InvestigationOptions(
                **{
                    name: getattr(args, name)
                    for name in ("pre_minutes", "post_minutes", "max_candidates", "max_evidence")
                }
            )
            result = explain(
                config.database, args.incident, options, mode=args.mode, model=args.model
            ).model_dump(mode="json")
            code = {"MODEL_UNAVAILABLE": 12, "MODEL_OUTPUT_REJECTED": 13}.get(
                result["explanation_status"], 0
            )
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False))
        return code
    except IncidentNotFound:
        print("Incident not found", file=sys.stderr)
        return 3
    except ToolError as exc:
        print(json.dumps(exc.as_dict(), sort_keys=True), file=sys.stderr)
        return exc.exit_code
    except (StorageError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "EXPLANATION_UNAVAILABLE",
                        "message": "Explanation operation failed; internal details are withheld.",
                    }
                }
            ),
            file=sys.stderr,
        )
        return 1
