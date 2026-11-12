"""Validated local ingestion: read-only dry-run or one explicit atomic Relate writer."""

from collections import defaultdict
from pathlib import Path

from pydantic import ValidationError

from traceweaver.ingestion_models import PROPERTY_NAMES, TIME_FIELDS, IngestionDocument
from traceweaver.local_files import local_path, parse_json_document, read_local_bytes
from traceweaver.schema import RELATIONSHIPS, ensure_schema
from traceweaver.source_integrity import inspect_bytes
from traceweaver.storage import GraphStore, StorageError
from traceweaver.temporal import parse_timestamp
from traceweaver.tool_errors import ToolError


def validate_document(data: bytes) -> IngestionDocument:
    try:
        return IngestionDocument.model_validate(parse_json_document(data))
    except ValidationError as exc:
        # Do not stringify ValidationError: it includes offending values and imported bodies.
        fields = {
            "nodes",
            "relationships",
            "source",
            "properties",
            "label",
            "type",
            "id",
            "dataset_id",
            "contract_version",
            "source_id",
            "kind",
            "declared_origin",
            "captured_at",
            "description",
        }
        fields |= set().union(*PROPERTY_NAMES.values())
        details = [
            {
                "location": [
                    part if isinstance(part, int) or part in fields else "<field>"
                    for part in error["loc"][:6]
                ],
                "code": error["type"],
            }
            for error in exc.errors(include_input=False, include_url=False)[:20]
        ]
        raise ToolError(
            "INVALID_INGESTION_DOCUMENT",
            "Ingestion contract validation failed.",
            validation_details=details,
            validation_error_count=exc.error_count(),
            validation_details_may_be_truncated=exc.error_count() > len(details),
        ) from None


def _edge_key(edge) -> tuple[str, str, str]:
    return edge.type, edge.source.id, edge.target.id


def _edge_properties(document: IngestionDocument, edge) -> dict:
    nodes = {(node.label, node.id): node for node in document.nodes}
    flags = [
        nodes[(ref.label, ref.id)].properties.get("demo") for ref in (edge.source, edge.target)
    ]
    marker = False if False in flags else None if None in flags else True
    return {"demo": marker, "dataset_id": document.dataset_id}


def _existing(store: GraphStore, document: IngestionDocument) -> tuple[dict, dict]:
    nodes, edges = {}, {}
    by_label, by_type = defaultdict(list), defaultdict(list)
    for node in document.nodes:
        by_label[node.label].append(node.id)
    for edge in document.relationships:
        by_type[edge.type].append([edge.source.id, edge.target.id])
    for label, identities in by_label.items():
        rows = store.execute(
            f"MATCH (n:{label}) WHERE n.id IN $ids "
            "RETURN properties(n) AS properties ORDER BY n.id LIMIT $limit",
            {"ids": identities, "limit": len(identities) + 1},
        )
        for row in rows:
            key = label, row["properties"]["id"]
            if key in nodes or len(rows) > len(identities):
                raise ToolError(
                    "INGEST_CONFLICT", "Existing graph contains ambiguous node identities.", 5
                )
            nodes[key] = row["properties"]
    for edge_type, pairs in by_type.items():
        source, target = RELATIONSHIPS[edge_type]
        rows = store.execute(
            f"UNWIND $pairs AS pair MATCH (a:{source})-[r:{edge_type}]->(b:{target}) "
            "WHERE a.id = pair[0] AND b.id = pair[1] "
            "RETURN a.id AS source_id, b.id AS target_id, properties(r) AS properties "
            "ORDER BY source_id, target_id LIMIT $limit",
            {"pairs": pairs, "limit": len(pairs) + 1},
        )
        for row in rows:
            key = edge_type, row["source_id"], row["target_id"]
            if key in edges or len(rows) > len(pairs):
                raise ToolError(
                    "INGEST_CONFLICT",
                    "Existing graph contains ambiguous relationship identities.",
                    5,
                )
            edges[key] = row["properties"]
    return nodes, edges


def _compatible(existing: dict, expected: dict) -> bool:
    return all(
        existing.get(key) == value and type(existing.get(key)) is type(value)
        for key, value in expected.items()
    )


def _node_expected(node) -> dict:
    return {**node.properties, "demo": node.properties.get("demo")}


def _assert_compatible(existing: dict, expected: dict) -> None:
    if not _compatible(existing, expected):
        raise ToolError(
            "INGEST_CONFLICT", "Existing record properties or ownership conflict with the batch.", 5
        )


def _check_preflight(document: IngestionDocument, nodes: dict, edges: dict) -> None:
    for node in document.nodes:
        if (node.label, node.id) in nodes:
            _assert_compatible(nodes[(node.label, node.id)], _node_expected(node))
    for edge in document.relationships:
        if _edge_key(edge) in edges:
            _assert_compatible(edges[_edge_key(edge)], _edge_properties(document, edge))


def ingest(
    input_path: str | Path,
    database: str | Path,
    *,
    apply: bool = False,
    allow_non_demo: bool = False,
    expected_sha256: str | None = None,
) -> dict:
    data = read_local_bytes(input_path)
    integrity = inspect_bytes(data, expected_sha256)
    if integrity.comparison_status == "MISMATCH":
        raise ToolError(
            "SOURCE_DIGEST_MISMATCH",
            "Independent expected digest does not match input bytes.",
            6,
            integrity=integrity.model_dump(),
        )
    document = validate_document(data)
    if not allow_non_demo and any(
        node.properties.get("demo") is not True for node in document.nodes
    ):
        raise ToolError(
            "NON_DEMO_REQUIRES_OPT_IN",
            "Non-demo or unknown-demo records require --allow-non-demo.",
            7,
            rejected_nodes=len(document.nodes),
            rejected_relationships=len(document.relationships),
            created_nodes=0,
            created_relationships=0,
        )
    path = local_path(database)
    if path.suffix.lower() != ".rl":
        raise ToolError("INVALID_DATABASE_PATH", "A persistent .rl target is required.")
    warnings = []
    for node in document.nodes:
        fields = TIME_FIELDS & node.properties.keys()
        if node.label in {"Incident", "Deployment", "Evidence"} and not (
            {"timestamp", "incident_started_at", "deployment_occurred_at", "observed_at"}
            & node.properties.keys()
        ):
            warnings.append(
                {"code": "MISSING_TIMESTAMP", "node_id": node.id, "field": "event_time"}
            )
        for field in sorted(fields):
            code = parse_timestamp(node.properties[field], field).warning_code
            if code:
                warnings.append({"code": code, "node_id": node.id, "field": field})
    counts = {
        "nodes_created": 0,
        "relationships_created": 0,
        "nodes_already_present": 0,
        "relationships_already_present": 0,
        "nodes_rejected": 0,
        "relationships_rejected": 0,
        "nodes_would_create": 0,
        "relationships_would_create": 0,
    }
    committed = False
    graph_counts = None
    try:
        # Relate may rewrite physical store bytes when closing a rolled-back writer.
        # Reject already-known conflicts read-only, then recheck after acquiring the writer.
        if apply and path.exists():
            with GraphStore(path) as preflight:
                nodes, edges = _existing(preflight, document)
                _check_preflight(document, nodes, edges)
        if not apply:
            existing_nodes, existing_edges = {}, {}
            if path.exists():
                with GraphStore(path) as store:
                    existing_nodes, existing_edges = _existing(store, document)
                    _check_preflight(document, existing_nodes, existing_edges)
                    graph_counts = store.counts()
            counts.update(
                nodes_already_present=len(existing_nodes),
                relationships_already_present=len(existing_edges),
                nodes_would_create=len(document.nodes) - len(existing_nodes),
                relationships_would_create=len(document.relationships) - len(existing_edges),
            )
        else:
            with GraphStore(path, read_only=False) as store:
                with store.transaction():
                    ensure_schema(store)
                    existing_nodes, existing_edges = _existing(store, document)
                    for node in document.nodes:
                        rows = store.execute(
                            f"MERGE (n:{node.label} {{id: $id}}) ON CREATE SET n += $properties "
                            "RETURN properties(n) AS properties LIMIT 1",
                            {"id": node.id, "properties": node.properties},
                        )
                        _assert_compatible(rows[0]["properties"], _node_expected(node))
                    for edge in document.relationships:
                        properties = _edge_properties(document, edge)
                        rows = store.execute(
                            f"MATCH (a:{edge.source.label} {{id: $source}}), "
                            f"(b:{edge.target.label} {{id: $target}}) "
                            f"MERGE (a)-[r:{edge.type}]->(b) ON CREATE SET r += $properties "
                            "RETURN properties(r) AS properties LIMIT 1",
                            {
                                "source": edge.source.id,
                                "target": edge.target.id,
                                "properties": properties,
                            },
                        )
                        _assert_compatible(rows[0]["properties"], properties)
                    graph_counts = store.counts()
                    counts.update(
                        nodes_created=len(document.nodes) - len(existing_nodes),
                        relationships_created=len(document.relationships) - len(existing_edges),
                        nodes_already_present=len(existing_nodes),
                        relationships_already_present=len(existing_edges),
                    )
                committed = True
    except ToolError as exc:
        exc.context.update(
            rejected_nodes=len(document.nodes),
            rejected_relationships=len(document.relationships),
            created_nodes=0,
            created_relationships=0,
            graph_counts=None,
        )
        raise
    except StorageError as exc:
        cause = exc.__cause__
        locked = "locked" in str(getattr(cause, "kind", "")).lower() or (
            cause is not None and "storage locked" in str(cause).lower()
        )
        raise ToolError(
            "GRAPH_STORE_LOCKED" if locked else "GRAPH_STORAGE_ERROR",
            "Selected .rl store is locked by another opener; no destructive retry was attempted."
            if locked
            else "Relate store is unavailable or rejected the operation.",
            10 if locked else 1,
            committed=committed,
            graph_counts=None,
        ) from None
    return {
        "ingestion_contract_version": "1.0",
        "dataset_id": document.dataset_id,
        "mode": "APPLY" if apply else "DRY_RUN",
        "committed": committed,
        "status": "COMMITTED" if committed else "VALIDATED_NOT_COMMITTED",
        "preflight": "COMMITTED_TRANSACTION"
        if committed
        else "EXISTING_STORE_COMPATIBLE"
        if graph_counts is not None
        else "STORE_ABSENT",
        "source_claim": document.source.model_dump(exclude={"description"}),
        "integrity": integrity.model_dump(),
        "input_counts": {
            "nodes": len(document.nodes),
            "relationships": len(document.relationships),
        },
        "counts": counts,
        "graph_counts": graph_counts,
        "warnings": warnings[:100],
        "warnings_may_be_truncated": len(warnings) > 100,
        "external_verification_status": "NOT_PERFORMED",
    }
