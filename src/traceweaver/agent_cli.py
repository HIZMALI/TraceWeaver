"""Separate opt-in agent CLI; existing traceweaver commands remain unchanged."""

import argparse
import json
import sys
from pathlib import Path
from typing import get_args

from traceweaver.agent import run_agent
from traceweaver.agent_models import (
    AgentRequest,
    AgentScopeRequest,
    Intent,
    canonical_agent_payload,
)
from traceweaver.agent_rehearsal import run_rehearsal
from traceweaver.agent_tools import create_context
from traceweaver.cli import bounded_integer
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.queries import IncidentNotFound
from traceweaver.storage import StorageError
from traceweaver.tool_errors import ToolError


def main(argv=None):
    parser = argparse.ArgumentParser(prog="traceweaver-agent")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--incident", required=True)
    parser.add_argument("--intent", choices=get_args(Intent), required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--rehearse", action="store_true")
    mode.add_argument("--model")
    parser.add_argument("--confirm-local", action="store_true")
    parser.add_argument("--canonical", action="store_true")
    defaults = InvestigationOptions()
    for name in ("pre_minutes", "post_minutes", "max_candidates", "max_evidence"):
        parser.add_argument(
            "--" + name.replace("_", "-"),
            default=getattr(defaults, name),
            type=bounded_integer(
                1 if name.startswith("max_") else 0, 100 if name.startswith("max_") else 1440
            ),
        )
    args = parser.parse_args(argv)
    if args.model and (not args.confirm_local or args.canonical):
        parser.error("Model execution requires --confirm-local; --canonical is rehearsal only")
    try:
        options = InvestigationOptions(
            **{k: getattr(args, k) for k in InvestigationOptions.model_fields}
        )
        source = create_context(args.database, args.incident, options)
        data = dict(
            incident_id=args.incident,
            options=options,
            source_fingerprint=source.source_fingerprint,
            intent=args.intent,
            confirmed=True,
        )
        action = (
            AgentRequest(**data, model_id=args.model) if args.model else AgentScopeRequest(**data)
        )
        report = (run_agent if args.model else run_rehearsal)(args.database, action)
        output = (
            canonical_agent_payload(report) if args.canonical else report.model_dump(mode="json")
        )
        print(json.dumps(output, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False))
        return 0 if report.agent_status in {"COMPLETED", "PARTIAL_CONTEXT", "ABSTAINED"} else 14
    except (ToolError, StorageError, IncidentNotFound, OSError, ValueError):
        print('{"error":{"code":"AGENT_OPERATION_FAILED"}}', file=sys.stderr)
        return 14


if __name__ == "__main__":
    raise SystemExit(main())
