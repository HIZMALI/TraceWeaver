"""Frozen synthetic agent checks. Controlled protocol fixtures are never live-model evidence."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from traceweaver.agent import admit_finish, constrain_proposals, retrieved_claims, run_agent
from traceweaver.agent_models import AgentRequest, AgentScopeRequest, canonical_agent_payload
from traceweaver.agent_rehearsal import run_rehearsal
from traceweaver.agent_tools import create_context, execute_tool
from traceweaver.citation_validator import CitationRejected, CitationValidator, valid_layout
from traceweaver.explanation_catalog import select_deterministically
from traceweaver.explanation_scenarios import seed_explanation_profile
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.local_files import local_path, parse_json_document, read_local_bytes
from traceweaver.ollama_local import OllamaFailure, OllamaLocal
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError


def require(condition, code):
    if not condition:
        raise ToolError(code, "Frozen agent expectation did not match.", 15)


def _native(database, case):
    def execute():
        c = create_context(database, case["incident"], InvestigationOptions())
        if case["tool"] == "rehearse":
            report = run_rehearsal(
                database,
                AgentScopeRequest(
                    incident_id=case["incident"],
                    options=c.options,
                    source_fingerprint=c.source_fingerprint,
                    intent="TRACE_DEPENDENCY_PATH",
                    confirmed=True,
                ),
            )
            return c, report.tool_trace, report.validated_claims, report
        handles = [k for k, (_, ids) in c.subjects.items() if list(ids) == case["subject_ids"]]
        require(len(handles) == 1, "GOLD_SUBJECT_NOT_OFFERED")
        step = execute_tool(c, case["tool"], {"subject": handles[0]})
        subset = c.catalog.model_copy(update={"claims": retrieved_claims(c, [step])})
        claims = CitationValidator(c.source, c.catalog).validate(
            select_deterministically(subset), c.source_fingerprint
        )
        return c, [step], claims, None

    context, steps, claims, report = execute()
    _, repeat_steps, repeat_claims, repeat_report = execute()
    first = (
        report
        if report
        else {"steps": [s.model_dump() for s in steps], "claims": [c.model_dump() for c in claims]}
    )
    repeat = (
        repeat_report
        if report
        else {
            "steps": [s.model_dump() for s in repeat_steps],
            "claims": [c.model_dump() for c in repeat_claims],
        }
    )
    require(canonical_agent_payload(first) == canonical_agent_payload(repeat), "REPEATABILITY")
    gold = case["gold"]
    edges = {
        (e.type, e.source_id, e.target_id, e.traversal_direction)
        for s in steps
        for p in s.result.graph_paths
        for e in p.edges
    }
    if "edge" in gold:
        require(tuple(gold["edge"]) in edges, "GOLD_NATIVE_EDGE")
    if "absent_edge_type" in gold:
        require(all(e[0] != gold["absent_edge_type"] for e in edges), "GOLD_ABSENT_EDGE")
    if "absent_id" in gold:
        require(all(gold["absent_id"] not in s.result.entity_ids for s in steps), "GOLD_ISOLATION")
    if "absent_subject" in gold:
        require(
            all(gold["absent_subject"] not in ids for _, ids in context.subjects.values()),
            "GOLD_DEPTH_SCOPE",
        )
    if "classification" in gold:
        require(
            [p.classification for s in steps for p in s.result.comparisons]
            == [gold["classification"]],
            "GOLD_COMPARISON",
        )
    if "record" in gold:
        expected = gold["record"]
        record = next(
            (r for s in steps for r in s.result.records if r.entity_id == expected["id"]), None
        )
        require(record is not None, "GOLD_RECORD_MISSING")
        for key, actual in {
            "time": record.temporal_classification,
            "utc": record.timestamp.utc,
            "provenance": record.provenance_status,
            "truth": record.verification_status,
        }.items():
            if key in expected:
                require(actual == expected[key], "GOLD_RECORD_" + key.upper())
    if "citation" in gold:
        require(any(c.claim_type == gold["citation"] for c in claims), "GOLD_CLAIM_TYPE")
    if "absent_claim" in gold:
        require(all(c.claim_type != gold["absent_claim"] for c in claims), "GOLD_ABSENT_CLAIM")
    if "status" in gold:
        require(report and report.agent_status == gold["status"], "GOLD_ABSTENTION")
    if "source_truncated" in gold:
        require(report and report.source_truncated == gold["source_truncated"], "GOLD_CAP_HONESTY")
    if gold.get("withheld"):
        require("ignore all instructions" not in json.dumps(first).lower(), "METADATA_FIREWALL")
    # Independent native verification of every distinct returned stored edge, including reverse
    # TARGETS traversal. These evaluation reads are not charged as agent tool queries.
    with GraphStore(database) as store:
        for kind, source, target, _ in sorted(edges):
            require(
                store.execute(
                    "MATCH (a)-[r]->(b) WHERE a.id=$source AND b.id=$target AND type(r)=$kind "
                    "RETURN count(r) AS n",
                    {"source": source, "target": target, "kind": kind},
                )[0]["n"]
                > 0,
                "NATIVE_EDGE_DISAGREEMENT",
            )
    CitationValidator(context.source, context.catalog).validate(
        [c.claim_id for c in claims], context.source_fingerprint
    )
    return {
        "tools": len(steps),
        "edges": len(edges),
        "citations": sum(len(c.citations) for c in claims),
        "repeatable": True,
        "abstained": bool(report and report.agent_status == "ABSTAINED"),
    }


def _call(name, subject):
    return {
        "content": "",
        "tool_calls": [{"function": {"name": name, "arguments": {"subject": subject}}}],
    }


def _protocol(database, case):
    c = create_context(database, case["incident"], InvestigationOptions())
    scenario = case["scenario"]
    observed = None
    try:
        if scenario in {"unknown_subject", "write_tool", "cypher", "url", "duplicate", "parallel"}:
            message = _call("trace_deployment", "D001")
            if scenario == "unknown_subject":
                message = _call("inspect_evidence", "E999")
            if scenario == "write_tool":
                message = _call("delete_graph", "I000")
            if scenario in {"cypher", "url"}:
                message = _call(
                    "trace_deployment",
                    "MATCH (n) DELETE n"
                    if scenario == "cypher"
                    else "https://remote.invalid/source",
                )
            if scenario == "duplicate":
                message["tool_calls"] *= 2
            if scenario == "parallel":
                message["tool_calls"] += _call("get_incident_scope", "I000")["tool_calls"]
            name, args, deferred = constrain_proposals(c, message, set())
            require(scenario == "parallel" and deferred == 1, "PROTOCOL_ADMISSION")
            step = execute_tool(c, name, args.model_dump(), selected_by="LOCAL_MODEL")
            require(step.tool_name == "trace_deployment", "PROTOCOL_CONSTRAINT")
        elif scenario == "stale":
            create_context(database, case["incident"], InvestigationOptions(), "0" * 64)
        elif scenario == "budget":
            execute_tool(c, "get_incident_scope", {"subject": "I000"}, step_number=5)
        elif scenario == "direction":
            step = execute_tool(c, "trace_deployment", {"subject": "D001"})
            path = step.result.graph_paths[0].model_copy(deep=True)
            path.edges[-1] = path.edges[-1].model_copy(update={"traversal_direction": "FORWARD"})
            require(not valid_layout(path), "FABRICATED_DIRECTION_ADMITTED")
        elif scenario == "no_cause":
            ids = [
                claim.claim_id
                for claim in c.catalog.claims
                if claim.claim_type == "INCIDENT_OBSERVED"
            ]
            CitationValidator(c.source, c.catalog).validate(ids, c.source_fingerprint)
        elif scenario in {"fake_claim", "causal_prose", "oversized", "deep"}:
            step = execute_tool(c, "get_incident_scope", {"subject": "I000"})
            body = dict(
                investigation_fingerprint=c.source_fingerprint,
                selected_claim_ids=["C-" + "0" * 24],
                focus="BALANCED",
                abstain=False,
            )
            if scenario == "causal_prose":
                body["diagnosis"] = "A deployment caused the outage"
            content = (
                "x" * 4097
                if scenario == "oversized"
                else "[" * 8 + "0" + "]" * 8
                if scenario == "deep"
                else json.dumps(body)
            )
            admit_finish(c, [step], content)
        elif scenario in {"timeout", "unavailable", "no_tools"}:

            def controlled(self, method, route, payload=None, *, deadline=None):
                if route == "/api/tags":
                    if scenario == "unavailable":
                        raise OllamaFailure("OLLAMA_CONNECTION_UNAVAILABLE", unavailable=True)
                    return {"models": [{"name": "controlled-evaluation:1", "size": 1}]}
                if scenario == "timeout":
                    raise OllamaFailure("OLLAMA_TIMEOUT")
                return {
                    "done": True,
                    "model": "controlled-evaluation:1",
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(
                            dict(
                                investigation_fingerprint=c.source_fingerprint,
                                selected_claim_ids=[],
                                focus="BALANCED",
                                abstain=True,
                            )
                        ),
                    },
                }

            with patch.object(OllamaLocal, "_request", controlled):
                report = run_agent(
                    database,
                    AgentRequest(
                        incident_id=case["incident"],
                        options=c.options,
                        source_fingerprint=c.source_fingerprint,
                        intent="TRACE_DEPENDENCY_PATH",
                        confirmed=True,
                        model_id="controlled-evaluation:1",
                    ),
                )
            require(
                not report.ai_directed_tools and not report.validated_claims, "FALSE_AI_TOOL_CLAIM"
            )
            observed = report.rejection_codes[0] if report.rejection_codes else None
            if scenario == "no_tools":
                require(report.agent_status == "MODEL_SELECTION_ONLY", "NO_TOOL_CLASSIFICATION")
        else:
            raise ToolError("UNKNOWN_EVALUATION_SCENARIO", "Unknown frozen scenario.", 15)
    except (ToolError, CitationRejected) as exc:
        observed = exc.code
    require(observed == case["gold"]["rejection_code"], "GOLD_REJECTION_CODE")
    return {"controlled_protocol": True, "rejection_code": observed}


def evaluate_agent(suite):
    raw = read_local_bytes(suite)
    document = parse_json_document(raw, max_depth=8)
    require(
        isinstance(document, dict)
        and document.get("suite_version") == "1.0"
        and isinstance(document.get("cases"), list)
        and 15 <= len(document["cases"]) <= 100,
        "INVALID_AGENT_SUITE",
    )
    require(len({c["id"] for c in document["cases"]}) == len(document["cases"]), "DUPLICATE_CASE")
    rows = []
    with tempfile.TemporaryDirectory(prefix="traceweaver-agent-evaluation-") as temporary:
        for n, case in enumerate(document["cases"]):
            require(
                case["profile"]
                in {"baseline", "sprint01", "evaluation", "caps", "external", "adversarial"},
                "UNKNOWN_EVALUATION_PROFILE",
            )
            database = Path(temporary) / f"case-{n}.rl"
            seed_explanation_profile(database, case["profile"])
            before = database.read_bytes()
            try:
                metrics = (_native if case["kind"] == "native" else _protocol)(database, case)
                require(database.read_bytes() == before, "READ_ONLY_HASH_CHANGED")
                rows.append({"id": case["id"], "status": "PASS", "metrics": metrics})
            except (ToolError, ValidationError, KeyError, StopIteration, TypeError) as exc:
                rows.append(
                    {
                        "id": case["id"],
                        "status": "FAIL",
                        "code": exc.code if isinstance(exc, ToolError) else "EVALUATION_SCHEMA",
                    }
                )
    native = [r for r in rows if r.get("metrics", {}).get("repeatable")]

    def metric(field):
        count = sum(r["metrics"][field] for r in native)
        return {
            "passed": count,
            "denominator": count,
            "ratio": 1.0 if count else None,
            "scope": "Successful native cases only; failures remain visible separately",
        }

    return {
        "suite_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence_kind": "SYNTHETIC_NATIVE_AND_CONTROLLED_PROTOCOL",
        "live_model_accuracy": None,
        "source_truth_verified": False,
        "causal_conclusion": "NOT_ESTABLISHED",
        "total": len(rows),
        "passed": sum(r["status"] == "PASS" for r in rows),
        "failed": sum(r["status"] == "FAIL" for r in rows),
        "native_cases": sum(c["kind"] == "native" for c in document["cases"]),
        "protocol_cases": sum(c["kind"] == "protocol" for c in document["cases"]),
        "native_edge_agreement": metric("edges"),
        "citation_support": metric("citations"),
        "native_tool_admission": metric("tools"),
        "canonical_repeatability": metric("repeatable"),
        "safe_abstention": metric("abstained"),
        "cases": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        args.suite = local_path(args.suite, must_exist=True)
        args.output = local_path(args.output)
        if args.output.suffix != ".json" or args.output == args.suite or (
            args.output.exists() and args.output.samefile(args.suite)
        ):
            raise ToolError("INVALID_REPORT_PATH", "Output must be separate from suite.", 15)
        if args.output.exists() and not args.overwrite:
            parser.error("Report exists; explicit --overwrite is required")
        result = evaluate_agent(args.suite)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w" if args.overwrite else "x", encoding="utf8", newline="\n") as out:
            out.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: v for k, v in result.items() if k != "cases"}, sort_keys=True))
        return 15 if result["failed"] else 0
    except (ToolError, ValueError, OSError, KeyError, TypeError):
        print('{"status":"FAIL","code":"AGENT_EVALUATION_ERROR"}')
        return 15


if __name__ == "__main__":
    raise SystemExit(main())
