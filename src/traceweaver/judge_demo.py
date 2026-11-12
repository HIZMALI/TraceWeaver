"""Build and inspect only the exact published synthetic graph, never a user store."""

import hashlib
import os
import re
import tempfile
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from traceweaver.investigation import investigate
from traceweaver.local_files import (
    canonical_json,
    local_path,
    parse_json_document,
    read_local_bytes,
)
from traceweaver.queries import incident_context
from traceweaver.seed import load_fixture, seed_database
from traceweaver.storage import GraphStore, StorageError
from traceweaver.tool_errors import ToolError

ARTIFACT_NAME = "traceweaver-demo.rl"
MANIFEST_NAME = "MANIFEST.json"
ARTIFACT_KIND = "TRACEWEAVER_SYNTHETIC_JUDGE_DEMO_V1"
FIXTURE_NAMES = ("demo_incidents.json", "sprint01_cases.json")
MANIFEST_KEYS = {
    "manifest_version",
    "artifact_kind",
    "artifact_filename",
    "artifact_size_bytes",
    "artifact_sha256",
    "relate_version",
    "synthetic_only",
    "graph_counts",
    "logical_graph_sha256",
    "fixture_sources",
    "contracts",
    "external_verification_status",
    "screening",
    "limitations",
}


def _sort_graph(nodes: list, relationships: list) -> dict:
    return {
        "nodes": sorted(nodes, key=lambda node: (node["label"], node["properties"]["id"])),
        "relationships": sorted(
            relationships,
            key=lambda edge: (
                edge["type"],
                edge["source"]["label"],
                edge["source"]["id"],
                edge["target"]["label"],
                edge["target"]["id"],
            ),
        ),
    }


def _screen_bytes(data: bytes) -> None:
    for encoding in ("utf-8", "utf-16-le"):
        if re.search(
            r"[A-Za-z]:[\\/](?:Users|Projects)[\\/]", data.decode(encoding, errors="ignore")
        ):
            raise ToolError(
                "PRIVATE_JUDGE_BYTES", "Artifact screening found a private path prefix."
            )


def _expected_graph() -> tuple[dict, list]:
    nodes, relationships, sources = [], [], []
    for name in FIXTURE_NAMES:
        path = files("traceweaver").joinpath("fixtures", name)
        fixture = load_fixture(path)
        labels = {node.properties["id"]: node.label for node in fixture.nodes}
        nodes += [
            {
                "label": node.label,
                "properties": {
                    key: value for key, value in node.properties.items() if value is not None
                },
            }
            for node in fixture.nodes
        ]
        relationships += [
            {
                "type": edge.type,
                "source": {"label": labels[edge.source], "id": edge.source},
                "target": {"label": labels[edge.target], "id": edge.target},
                "properties": {"demo": True, "dataset_id": fixture.dataset_id},
            }
            for edge in fixture.relationships
        ]
        sources.append(
            {
                "name": "fixtures/" + name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "demo_fixture_schema_version": fixture.schema_version,
            }
        )
    return _sort_graph(nodes, relationships), sources


def _inspect_store(path: Path, expected: dict) -> tuple[dict, str]:
    try:
        with GraphStore(path) as store:
            counts = store.counts()
            if counts["node_count"] > 2000 or counts["relationship_count"] > 4000:
                raise ToolError(
                    "UNSAFE_JUDGE_GRAPH", "Judge graph exceeds bounded inspection limits."
                )
            node_rows = store.execute(
                "MATCH (n) RETURN labels(n) AS labels, properties(n) AS properties LIMIT 2001"
            )
            edge_rows = store.execute(
                "MATCH (a)-[r]->(b) RETURN labels(a) AS source_labels, a.id AS source_id, "
                "labels(b) AS target_labels, b.id AS target_id, type(r) AS type, "
                "properties(r) AS properties LIMIT 4001"
            )
            if any(len(row["labels"]) != 1 for row in node_rows) or any(
                len(row["source_labels"]) != 1 or len(row["target_labels"]) != 1
                for row in edge_rows
            ):
                raise ToolError(
                    "UNSAFE_JUDGE_GRAPH",
                    "Judge graph labels differ from the published synthetic schema.",
                )
            graph = _sort_graph(
                [{"label": row["labels"][0], "properties": row["properties"]} for row in node_rows],
                [
                    {
                        "type": row["type"],
                        "source": {"label": row["source_labels"][0], "id": row["source_id"]},
                        "target": {"label": row["target_labels"][0], "id": row["target_id"]},
                        "properties": row["properties"],
                    }
                    for row in edge_rows
                ],
            )
            if graph != expected:
                raise ToolError(
                    "UNSAFE_JUDGE_GRAPH",
                    "Judge store does not exactly match the published synthetic fixtures.",
                )
            for record in graph["nodes"] + graph["relationships"]:
                properties = record["properties"]
                if properties.get("demo") is not True:
                    raise ToolError(
                        "NON_SYNTHETIC_JUDGE_DATA",
                        "Every included graph record must be explicitly synthetic.",
                    )
                if properties.get("source_ref") and not properties["source_ref"].startswith(
                    "demo://"
                ):
                    raise ToolError(
                        "PRIVATE_JUDGE_SOURCE",
                        "Only published demo source references are admitted.",
                    )
                if properties.get("source") and not properties["source"].startswith("demo-"):
                    raise ToolError(
                        "PRIVATE_JUDGE_SOURCE", "Only published demo source names are admitted."
                    )
                for value in properties.values():
                    if isinstance(value, str) and re.search(
                        r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]|^\\\\|sk-[A-Za-z0-9]{24,}|"
                        r"-----BEGIN .*PRIVATE KEY|"
                        r"(?:api[_-]?key|access[_-]?token|password)\s*[:=]",
                        value,
                        re.I,
                    ):
                        raise ToolError(
                            "PRIVATE_JUDGE_SOURCE",
                            "Judge source screening rejected a private-path or credential pattern.",
                        )
            context = incident_context(store, "INC-001")
            review = investigate(store, "CASE-INC")
            if not context.context_paths or review.causal_conclusion != "NOT_ESTABLISHED":
                raise ToolError(
                    "JUDGE_QUERY_FAILURE", "Read-only demo context verification failed."
                )
    except StorageError:
        raise ToolError(
            "JUDGE_STORAGE_ERROR", "Cannot inspect the selected Relate judge artifact.", 1
        ) from None
    return counts, hashlib.sha256(canonical_json(graph).encode()).hexdigest()


def verify_judge_demo(output_dir: str | Path) -> dict:
    output = local_path(output_dir, must_exist=True)
    artifact = output / ARTIFACT_NAME
    manifest = parse_json_document(read_local_bytes(output / MANIFEST_NAME))
    data = read_local_bytes(artifact)
    _screen_bytes(data)
    if (
        set(manifest) != MANIFEST_KEYS
        or manifest.get("external_verification_status") != "NOT_PERFORMED"
        or manifest.get("artifact_kind") != ARTIFACT_KIND
        or manifest.get("manifest_version") != "1.0"
        or manifest.get("artifact_filename") != ARTIFACT_NAME
        or manifest.get("synthetic_only") is not True
        or manifest.get("artifact_sha256") != hashlib.sha256(data).hexdigest()
        or manifest.get("artifact_size_bytes") != len(data)
    ):
        raise ToolError(
            "INVALID_JUDGE_MANIFEST", "Generated-artifact identity, size, or digest does not match."
        )
    expected, sources = _expected_graph()
    counts, logical_hash = _inspect_store(artifact, expected)
    if (
        manifest.get("graph_counts") != counts
        or manifest.get("logical_graph_sha256") != logical_hash
        or manifest.get("fixture_sources") != sources
        or manifest.get("relate_version") != "1.0.0"
    ):
        raise ToolError(
            "INVALID_JUDGE_MANIFEST", "Judge manifest does not match the verified published graph."
        )
    return manifest


def _publish(path: Path, data: bytes, replace: bool) -> None:
    if not replace:
        with path.open("xb") as destination:
            destination.write(data)
        return
    # Replacement is reachable only after exact generated-artifact ownership/content checks.
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=".traceweaver-publish-", delete=False
    ) as temp:
        temporary_path = Path(temp.name)
        temp.write(data)
    try:
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def build_judge_demo(output_dir: str | Path, *, force: bool = False) -> dict:
    if version("relate-db") != "1.0.0":
        raise ToolError("UNSUPPORTED_ENGINE", "Judge demo requires relate-db 1.0.0.")
    output = local_path(output_dir)
    if output.suffix.lower() == ".rl" or (output.exists() and not output.is_dir()):
        raise ToolError(
            "INVALID_JUDGE_OUTPUT", "Select a fresh output directory, not a database file."
        )
    target = local_path(output / ARTIFACT_NAME)
    manifest_path = local_path(output / MANIFEST_NAME)
    present = target.exists() or manifest_path.exists()
    if present:
        if not force:
            raise ToolError(
                "JUDGE_OUTPUT_EXISTS",
                "Judge output exists; --force requires a verified generated bundle.",
            )
        try:
            verify_judge_demo(output)
        except ToolError:
            raise ToolError(
                "UNSAFE_JUDGE_REPLACEMENT", "--force requires an intact verified generated bundle."
            ) from None
    expected, sources = _expected_graph()
    with tempfile.TemporaryDirectory(prefix="traceweaver-judge-build-") as temp:
        database = Path(temp) / ARTIFACT_NAME
        for name in FIXTURE_NAMES:
            seed_database(database, files("traceweaver").joinpath("fixtures", name))
        counts, logical_hash = _inspect_store(database, expected)
        data = database.read_bytes()  # Every writer and reader is closed before hashing.
    if len(data) > 8 * 1024 * 1024:
        raise ToolError(
            "JUDGE_ARTIFACT_TOO_LARGE", "Synthetic judge artifact exceeds the 8 MiB packaging cap."
        )
    _screen_bytes(data)
    manifest = {
        "manifest_version": "1.0",
        "artifact_kind": ARTIFACT_KIND,
        "artifact_filename": ARTIFACT_NAME,
        "artifact_size_bytes": len(data),
        "artifact_sha256": hashlib.sha256(data).hexdigest(),
        "relate_version": "1.0.0",
        "synthetic_only": True,
        "graph_counts": counts,
        "logical_graph_sha256": logical_hash,
        "fixture_sources": sources,
        "contracts": {"demo_fixture_versions": [1, 2], "investigation": "Sprint 01 unchanged"},
        "external_verification_status": "NOT_PERFORMED",
        "screening": [
            "Exact published fixture graph",
            "Every node and edge demo=true",
            "Demo-only source references",
            "Private-path and credential-pattern checks",
        ],
        "limitations": (
            "Bounded pattern/content checks are not a perfect secrets audit. "
            "A digest establishes byte equality only."
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    try:
        _publish(target, data, present)
        _publish(manifest_path, canonical_json(manifest).encode("utf-8"), present)
    except OSError:
        raise ToolError(
            "JUDGE_PUBLISH_ERROR",
            "Cannot publish the generated judge bundle; inspect the selected output.",
            1,
        ) from None
    return verify_judge_demo(output)
