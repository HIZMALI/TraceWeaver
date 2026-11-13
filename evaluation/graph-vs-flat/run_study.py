"""Frozen illustrative retrieval study; no runtime predictions are used as gold."""

import argparse
import hashlib
import json
import math
import platform
import re
import statistics
import tempfile
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from traceweaver.investigation import investigate
from traceweaver.investigation_models import InvestigationOptions
from traceweaver.local_files import canonical_json
from traceweaver.queries import IncidentNotFound
from traceweaver.seed import seed_database
from traceweaver.storage import GraphStore

ROOT = Path(__file__).resolve().parents[2]
GOLD = Path(__file__).with_name("questions.json")
GOLD_SHA256 = "53e089d433a5f9de6c00105aa7837e1d9ae29016750ef6802f4cc0fde095db81"
STOP = set(
    "which are is the to a an of for in on with through and or at from have has under".split()
)
SINGULAR = dict(
    zip(
        (
            "deployments",
            "services",
            "changes",
            "records",
            "dependencies",
            "observations",
            "candidates",
            "targets",
        ),
        (
            "deployment",
            "service",
            "change",
            "record",
            "dependency",
            "observation",
            "candidate",
            "target",
        ),
        strict=True,
    )
)


def tokens(text):
    result = []
    for word in re.findall(r"[a-z0-9]+(?:[-.:][a-z0-9]+)*", text.lower()):
        for token in [word, *re.split(r"[-.:]", word)] if re.search(r"[-.:]", word) else [word]:
            token = SINGULAR.get(token, token)
            if token not in STOP:
                result.append(token)
    return result


class FlatIndex:
    def __init__(self, nodes, edges):
        self.nodes = {n["properties"]["id"]: n for n in nodes}
        self.edges = edges
        self.documents = {}
        for identity, node in self.nodes.items():
            adjacent = [e for e in edges if identity in (e["source"], e["target"])]
            self.documents[identity] = Counter(
                tokens(canonical_json({"entity": node, "edges": adjacent}))
            )
        self.average = statistics.mean(sum(d.values()) for d in self.documents.values())
        self.df = Counter(token for doc in self.documents.values() for token in doc)

    def search(self, question, k=5):
        anchor = self.nodes.get(question["incident"])
        if not anchor or anchor["label"] != "Incident" or question["operation"] == "proven_cause":
            return []
        terms = set(tokens(question["question"]))
        ranked = []
        for identity, doc in self.documents.items():
            if self.nodes[identity]["label"] != question["label"]:
                continue
            length = sum(doc.values())
            score = 0.0
            for term in terms:
                frequency = doc[term]
                if frequency:
                    idf = math.log(
                        1 + (len(self.documents) - self.df[term] + 0.5) / (self.df[term] + 0.5)
                    )
                    score += (
                        idf
                        * frequency
                        * 2.2
                        / (frequency + 1.2 * (0.25 + 0.75 * length / self.average))
                    )
            if score > 0:
                ranked.append((identity, score))
        cap = (
            question.get("options", {}).get("max_candidates", 100)
            if question["label"] == "Deployment"
            else 100
        )
        return [
            identity for identity, _ in sorted(ranked, key=lambda v: (-v[1], v[0]))[: min(k, cap)]
        ]


def selected_ids(source, operation):
    if operation == "candidates":
        return {c.deployment_id for c in source.candidates}
    if operation == "direct_candidates":
        return {c.deployment_id for c in source.candidates if c.dependency_depth == 0}
    if operation in {"before", "at_onset", "after", "unknown"}:
        return {
            c.deployment_id
            for c in source.candidates
            if c.temporal_classification == operation.upper()
        }
    if operation == "changes":
        return {x.change_id for c in source.candidates for x in c.changes}
    if operation == "evidence":
        return {e.evidence_id for e in source.evidence}
    if operation == "orphan":
        return {e.evidence_id for e in source.evidence if not e.observed_service_ids}
    if operation == "conflict":
        return {
            identity
            for c in source.contradictions
            if c.classification == "CONFLICTING_OBSERVATIONS"
            for identity in c.evidence_ids
        }
    if operation == "availability":
        return {
            e.evidence_id
            for e in source.evidence
            if "CASE-API" in e.observed_service_ids
            and e.properties.get("service_id") == "CASE-API"
            and e.properties.get("signal_key") == "availability"
        }
    if operation == "proven_cause":
        assert source.causal_conclusion == "NOT_ESTABLISHED"
        return set()
    raise ValueError("Unsupported frozen operation")


def graph_read(database, question):
    try:
        with GraphStore(database) as store:
            source = investigate(
                store, question["incident"], InvestigationOptions(**question.get("options", {}))
            )
        return selected_ids(source, question["operation"]), source
    except IncidentNotFound:
        return set(), None


def proof_edges(database, source, ids):
    if source is None:
        return []
    paths = [p for c in source.candidates if c.deployment_id in ids for p in c.graph_paths]
    paths += [x.graph_path for c in source.candidates for x in c.changes if x.change_id in ids]
    paths += [p for e in source.evidence if e.evidence_id in ids for p in e.graph_paths]
    keys = set()
    for path in paths:
        assert len(path.node_ids) == len(path.edges) + 1
        for index, edge in enumerate(path.edges):
            pair = path.node_ids[index : index + 2]
            if edge.traversal_direction == "REVERSE":
                pair = pair[::-1]
            assert pair == [edge.source_id, edge.target_id]
            keys.add((edge.type, edge.source_id, edge.target_id))
    edges = [
        {"key": str(n), "type": kind, "source": source, "target": target}
        for n, (kind, source, target) in enumerate(sorted(keys))
    ]
    if edges:
        with GraphStore(database) as store:
            rows = store.execute(
                "UNWIND $edges AS e MATCH (a)-[r]->(b) "
                "WHERE a.id=e.source AND b.id=e.target AND type(r)=e.type "
                "RETURN DISTINCT e.key AS key",
                {"edges": edges},
            )
        assert len(rows) == len(edges), "A proposed proof edge is absent from native Relate"
    return [{k: v for k, v in e.items() if k != "key"} for e in edges]


def metrics(predicted, expected):
    p, e = set(predicted), set(expected)
    return {
        "tp": len(p & e),
        "fp": len(p - e),
        "fn": len(e - p),
        "precision": len(p & e) / len(p) if p else None,
        "recall": len(p & e) / len(e) if e else None,
        "exact": p == e,
    }


def timings(values):
    return {
        "first_read_ms": values[0],
        "warm_n": len(values) - 1,
        "warm_median_ms": statistics.median(values[1:]),
        "warm_p95_nearest_rank_ms": sorted(values[1:])[math.ceil((len(values) - 1) * 0.95) - 1],
    }


def run_study():
    assert hashlib.sha256(GOLD.read_bytes()).hexdigest() == GOLD_SHA256, "Frozen gold changed"
    suite = json.loads(GOLD.read_bytes())
    nodes, edges, hashes = [], [], {}
    for name in suite["fixtures"]:
        path = ROOT / "fixtures" / name
        raw = path.read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
        fixture = json.loads(raw)
        nodes += fixture["nodes"]
        edges += fixture["relationships"]
    index = FlatIndex(nodes, edges)
    results = []
    with tempfile.TemporaryDirectory(prefix="traceweaver-retrieval-study-") as temporary:
        database = Path(temporary) / "study.rl"
        for name in suite["fixtures"]:
            seed_database(database, ROOT / "fixtures" / name)
        before = database.read_bytes()
        with GraphStore(database) as store:
            counts = store.counts()
        for q in suite["questions"]:
            graph_times, flat_times = [], []
            for _ in range(6):
                start = time.perf_counter_ns()
                graph_ids, source = graph_read(database, q)
                graph_times.append(round((time.perf_counter_ns() - start) / 1e6, 6))
                start = time.perf_counter_ns()
                flat_ids = index.search(q, suite["flat_top_k"])
                flat_times.append(round((time.perf_counter_ns() - start) / 1e6, 6))
            truncated = bool(source and source.results_may_be_truncated)
            cap_matches = (
                truncated == q["expected_source_truncated"]
                if "expected_source_truncated" in q
                else None
            )
            results.append(
                {
                    "id": q["id"],
                    "question": q["question"],
                    "expected_ids": q["expected_ids"],
                    "graph": {
                        "ids": sorted(graph_ids),
                        "metrics": metrics(graph_ids, q["expected_ids"]),
                        "matched_native_edges": proof_edges(database, source, graph_ids),
                        "timing": timings(graph_times),
                        "source_truncated": truncated,
                        "expected_cap_matches": cap_matches,
                    },
                    "flat": {
                        "ids": flat_ids,
                        "metrics": metrics(flat_ids, q["expected_ids"]),
                        "record_edge_facts": [
                            e for e in edges if e["source"] in flat_ids or e["target"] in flat_ids
                        ],
                        "timing": timings(flat_times),
                    },
                }
            )
        assert before == database.read_bytes()
    return {
        "study_version": "1.0",
        "selector_revision": "1.1",
        "recorded_utc": datetime.now(UTC).isoformat(),
        "gold_sha256": GOLD_SHA256,
        "fixture_sha256": hashes,
        "native_counts": counts,
        "python": platform.python_version(),
        "os": platform.platform(),
        "processor": platform.processor(),
        "method": "Same public node fields/all edge facts; structured native selectors vs "
        "BM25-like unjoined records. First read plus five repeated reads; setup/index/proof "
        "audit excluded. See README for intent asymmetry.",
        "graph_exact_cases": sum(r["graph"]["metrics"]["exact"] for r in results),
        "flat_exact_cases": sum(r["flat"]["metrics"]["exact"] for r in results),
        "cases": results,
    }


def markdown(report):
    lines = [
        "# Actual connected-retrieval study results",
        "",
        report["method"],
        "",
        f"Gold SHA-256: `{report['gold_sha256']}`. Native store: {report['native_counts']}.",
        f"Exact ID sets: graph {report['graph_exact_cases']}/14; "
        f"flat {report['flat_exact_cases']}/14.",
        "",
        "No production/general accuracy or root-cause claim. Empty denominators are null in JSON.",
        "R13 has an invalid frozen cap-order assumption; retain its raw mismatch for audit. "
        "See ERRATA.md; thirteen other frozen questions are eligible for interpretation.",
        "",
        "| Case | Gold IDs | Native IDs | Flat IDs | Graph TP/FP/FN | Flat TP/FP/FN | "
        "Warm graph / flat median ms |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
        g, f = row["graph"], row["flat"]

        def ids(values):
            return ", ".join(values) or "∅"

        def score(v):
            return "/".join(str(v["metrics"][k]) for k in ("tp", "fp", "fn"))

        lines.append(
            f"| {row['id']} | {ids(row['expected_ids'])} | {ids(g['ids'])} | {ids(f['ids'])} | "
            f"{score(g)} | {score(f)} | {g['timing']['warm_median_ms']:.4f} / "
            f"{f['timing']['warm_median_ms']:.4f} |"
        )
    lines += [
        "",
        "Every graph matched edge was rechecked in native Relate after timing; exact triples, "
        "per-case precision/recall and descriptive timing p95 are in results.json. Flat edge "
        "facts are adjacent record facts, not a joined incident proof path.",
        "",
        "This small authored task set favors explicit relational operations. The graph arm "
        "receives structured intent; the lexical arm gets text plus anchor/type/cap. A flat "
        "join engine can express the same relationships. Lexical retrieval may be much faster "
        "and has weaker relational scope; no universal winner is inferred.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--markdown", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.markdown.exists():
        parser.error("Choose new output paths; existing reports are never overwritten")
    report = run_study()
    args.output.write_text(canonical_json(report), encoding="utf8", newline="\n")
    args.markdown.write_text(markdown(report), encoding="utf8", newline="\n")
    print(
        json.dumps(
            {
                "graph_exact": report["graph_exact_cases"],
                "flat_exact": report["flat_exact_cases"],
                "questions": 14,
            }
        )
    )


if __name__ == "__main__":
    main()
