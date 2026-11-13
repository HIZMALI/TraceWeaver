"""Fixed read-only tools: snapshot admission followed by actual bounded native Cypher."""

import hashlib
import time
from dataclasses import dataclass

from traceweaver.agent_models import AgentRecord, AgentStep, NativeToolResult, ToolArguments
from traceweaver.citation_validator import valid_layout
from traceweaver.contradictions import detect_contradictions
from traceweaver.dashboard import display_label, display_time, read_entity_kinds
from traceweaver.dashboard_models import ViewComparison
from traceweaver.explanation_catalog import build_catalog, fingerprint, safe_identity
from traceweaver.explanation_models import ProofPath
from traceweaver.investigation import candidate_path, investigate
from traceweaver.local_files import read_local_bytes
from traceweaver.provenance import evidence_context, graph_properties
from traceweaver.queries import INCIDENT_LOOKUP
from traceweaver.storage import GraphStore
from traceweaver.tool_errors import ToolError

TOOL_NAMES = (
    "get_incident_scope",
    "trace_deployment",
    "inspect_evidence",
    "compare_observations",
    "inspect_gaps",
)
TRACE_QUERY = """
MATCH p=(i:Incident {id:$incident_id})-[:AFFECTS]->(:Service)
 -[:DEPENDS_ON*0..3]->(target:Service)<-[:TARGETS]-(d:Deployment)
WHERE d.id=$deployment_id AND target.id=$target_id
 AND all(n IN nodes(p) WHERE single(m IN nodes(p) WHERE elementId(m)=elementId(n)))
WITH d,target,min([length(p),[n IN nodes(p)|n.id]]) AS chosen
RETURN properties(d) AS deployment, chosen[1] AS node_ids LIMIT 2
"""


def database_digest(database):
    # The fixed 8 MiB local-file bound is separate from the engine's working-memory cost.
    return hashlib.sha256(read_local_bytes(database)).hexdigest()


class ToolStore(GraphStore):
    def __init__(self, database, context=None):
        super().__init__(database, read_only=True)
        self.query_count = 0
        self.context = context

    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            if self.context is not None:
                self.context.native_queries += self.query_count

    def execute(self, statement, params=None):
        if self.query_count >= 8:
            raise ToolError("AGENT_QUERY_BUDGET", "Native tool query budget exhausted.")
        self.query_count += 1
        return super().execute(statement, params)


@dataclass
class AgentContext:
    database: object
    source: object
    catalog: object
    source_fingerprint: str
    database_digest: str
    options: object
    subjects: dict
    node_handles: dict
    subjects_truncated: bool
    native_queries: int

    def guard(self):
        if database_digest(self.database) != self.database_digest:
            raise ToolError("STALE_SNAPSHOT", "Source changed; refresh the investigation.")


def create_context(database, incident_id, options, expected_fingerprint=None):
    before = database_digest(database)
    with ToolStore(database) as store:
        source = investigate(store, incident_id, options)
        kinds = read_entity_kinds(store, source)
        queries = store.query_count
    if before != database_digest(database):
        raise ToolError("STALE_SNAPSHOT", "Source changed during snapshot creation.")
    source_fingerprint = fingerprint(source)
    if expected_fingerprint is not None and expected_fingerprint != source_fingerprint:
        raise ToolError("STALE_SNAPSHOT", "Requested source fingerprint is stale.")
    catalog = build_catalog(source)
    if any(not safe_identity(identity) for identity in kinds):
        raise ToolError("AGENT_UNSAFE_IDENTITY", "Returned identity cannot be exposed.")
    subjects = {"I000": ("incident", (source.incident_id,))}
    for n, c in enumerate(source.candidates[:8]):
        subjects[f"D{n:03}"] = ("deployment", (c.deployment_id, c.target_service_id))
    for n, e in enumerate(source.evidence[:8]):
        subjects[f"E{n:03}"] = ("evidence", (e.evidence_id,))
    for n, p in enumerate(source.contradictions[:5]):
        subjects[f"P{n:03}"] = ("comparison", tuple(p.evidence_ids))
    return AgentContext(
        database,
        source,
        catalog,
        source_fingerprint,
        before,
        options,
        subjects,
        {identity: f"N{n:03}" for n, identity in enumerate(sorted(kinds))},
        len(source.candidates) > 8 or len(source.evidence) > 8 or len(source.contradictions) > 5,
        queries,
    )


def _proof(path):
    value = ProofPath.model_validate(path.model_dump())
    if not valid_layout(value):
        raise ToolError("AGENT_INVALID_DIRECTION", "Stored path direction is incompatible.")
    return value


def _record(item, kind):
    timestamp = item.deployment_occurred_at if kind == "deployment" else item.evidence_observed_at
    return AgentRecord(
        entity_id=item.deployment_id if kind == "deployment" else item.evidence_id,
        timestamp=display_time(timestamp),
        temporal_classification=item.temporal_classification,
        provenance_status=None if kind == "deployment" else item.provenance_status,
        verification_status=None if kind == "deployment" else item.verification_status,
    )


def _native_evidence(store, context, identity):
    rows = store.execute(
        "MATCH (:Incident {id:$incident_id})-[:HAS_EVIDENCE]->(e:Evidence {id:$evidence_id}) "
        "RETURN properties(e) AS evidence LIMIT 2",
        {"incident_id": context.source.incident_id, "evidence_id": identity},
    )
    if len(rows) != 1:
        raise ToolError("AGENT_SCOPE_MISMATCH", "Native evidence membership is incompatible.")
    native = graph_properties(rows[0]["evidence"])
    expected = next(e for e in context.source.evidence if e.evidence_id == identity)
    if native != expected.properties:
        raise ToolError("STALE_SNAPSHOT", "Native evidence changed.")
    neighbors = store.execute(
        "MATCH (:Incident {id:$incident_id})-[:HAS_EVIDENCE]->(e:Evidence {id:$evidence_id})"
        "-[:OBSERVED_ON]->(s:Service) RETURN DISTINCT s.id AS id ORDER BY id LIMIT 101",
        {"incident_id": context.source.incident_id, "evidence_id": identity},
    )
    ids = sorted({r["id"] for r in neighbors if r["id"] in expected.observed_service_ids})
    if ids != expected.observed_service_ids:
        raise ToolError("AGENT_SCOPE_MISMATCH", "Native observation membership differs.")
    item = evidence_context(
        context.source.incident_id, native, ids, context.source.incident_time, context.options
    )
    return item, len(neighbors) > len(ids)


def _scope(store, context, ids):
    rows = store.execute(INCIDENT_LOOKUP, {"incident_id": ids[0]})
    if len(rows) != 1 or graph_properties(rows[0]["incident"]) != context.source.incident:
        raise ToolError("STALE_SNAPSHOT", "Incident scope changed.")
    services = store.execute(
        "MATCH (i:Incident {id:$incident_id})-[:AFFECTS]->(s:Service) "
        "RETURN DISTINCT s.id AS id ORDER BY id LIMIT 101",
        {"incident_id": ids[0]},
    )
    admitted = {s["id"] for s in context.source.affected_services}
    if not admitted.issubset({s["id"] for s in services}):
        raise ToolError("AGENT_SCOPE_MISMATCH", "Affected scope changed.")
    paths = [
        ProofPath(
            node_ids=[ids[0], s],
            edges=[
                {
                    "type": "AFFECTS",
                    "source_id": ids[0],
                    "target_id": s,
                    "traversal_direction": "FORWARD",
                }
            ],
        )
        for s in sorted(admitted)
    ]
    incident = AgentRecord(
        entity_id=ids[0],
        timestamp=display_time(context.source.incident_time),
        temporal_classification="AT_ONSET" if context.source.incident_time.utc else "UNKNOWN",
    )
    return paths, [incident], [], [], len(services) > len(admitted)


def _deployment(store, context, ids):
    rows = store.execute(
        TRACE_QUERY,
        {"incident_id": context.source.incident_id, "deployment_id": ids[0], "target_id": ids[1]},
    )
    expected = next(
        c for c in context.source.candidates if (c.deployment_id, c.target_service_id) == ids
    )
    if len(rows) != 1 or graph_properties(rows[0]["deployment"]) != expected.properties:
        raise ToolError("AGENT_SCOPE_MISMATCH", "Native deployment scope differs.")
    path = candidate_path(rows[0]["node_ids"])
    if path.model_dump() != expected.graph_paths[0].model_dump():
        raise ToolError("AGENT_SCOPE_MISMATCH", "Native candidate path differs.")
    changes = store.execute(
        "MATCH (d:Deployment {id:$deployment_id})-[:INCLUDES_CHANGE]->(c:Change) "
        "RETURN DISTINCT c.id AS id ORDER BY id LIMIT 101",
        {"deployment_id": ids[0]},
    )
    actual = {r["id"] for r in changes}
    if not set(expected.change_ids).issubset(actual):
        raise ToolError("AGENT_SCOPE_MISMATCH", "Included changes differ.")
    paths = [path] + [c.graph_path for c in expected.changes]
    return paths, [_record(expected, "deployment")], [], [], len(actual) > len(expected.change_ids)


def _evidence(store, context, ids):
    item, cut = _native_evidence(store, context, ids[0])
    return item.graph_paths, [_record(item, "evidence")], [], [w.code for w in item.warnings], cut


def _comparison(store, context, ids):
    first, cut_a = _native_evidence(store, context, ids[0])
    second, cut_b = _native_evidence(store, context, ids[1])
    pairs, _, cut = detect_contradictions([first, second])
    if len(pairs) != 1 or not any(
        pairs[0].model_dump() == p.model_dump() for p in context.source.contradictions
    ):
        raise ToolError("AGENT_COMPARISON_MISMATCH", "Structured native comparison differs.")
    pair = pairs[0]
    view = ViewComparison(
        evidence_ids=pair.evidence_ids,
        service_id=pair.service_id,
        signal_key=display_label(pair.signal_key),
        environment=display_label(pair.environment),
        overlap_window=pair.overlap_window,
        observed_states=pair.observed_states,
        classification=pair.classification,
    )
    return (
        first.graph_paths + second.graph_paths,
        [_record(first, "evidence"), _record(second, "evidence")],
        [view],
        [],
        cut or cut_a or cut_b,
    )


def _gaps(store, context, ids):
    fresh = investigate(store, ids[0], context.options)
    if fingerprint(fresh) != context.source_fingerprint:
        raise ToolError("STALE_SNAPSHOT", "Native gap context changed.")
    paths = [p for c in fresh.candidates[:3] for p in c.graph_paths]
    paths += [p for e in fresh.evidence[:4] for p in e.graph_paths]
    return paths, [], [], [g.code for g in fresh.evidence_gaps], fresh.results_may_be_truncated


HANDLERS = {
    "get_incident_scope": ("incident", _scope),
    "trace_deployment": ("deployment", _deployment),
    "inspect_evidence": ("evidence", _evidence),
    "compare_observations": ("comparison", _comparison),
    "inspect_gaps": ("incident", _gaps),
}


def execute_tool(context, tool_name, arguments, *, step_number=1, selected_by="DETERMINISTIC_PLAN"):
    if type(step_number) is not int or not 1 <= step_number <= 4:
        raise ToolError("AGENT_TOOL_BUDGET", "At most four native steps are admitted.")
    if tool_name not in HANDLERS:
        raise ToolError("AGENT_TOOL_REJECTED", "Only fixed native tools are admitted.")
    arguments = ToolArguments.model_validate(arguments)
    expected_kind, handler = HANDLERS[tool_name]
    subject = context.subjects.get(arguments.subject)
    if not subject or subject[0] != expected_kind:
        raise ToolError("AGENT_SUBJECT_REJECTED", "Subject is outside offered incident scope.")
    context.guard()
    start = time.monotonic()
    with ToolStore(context.database, context=context) as store:
        paths, records, comparisons, gaps, truncated = handler(store, context, subject[1])
        paths = [_proof(p) for p in paths]
        truncated |= len(paths) > 8 or len(records) > 8 or len(set(gaps)) > 20
        paths = paths[:8]
        records = records[:8]
        ids = sorted(
            {*subject[1], *[r.entity_id for r in records], *[v for p in paths for v in p.node_ids]}
        )
        keys = sorted({(e.type, e.source_id, e.target_id) for p in paths for e in p.edges})
        edges = [
            {"key": str(n), "type": k, "source": s, "target": t} for n, (k, s, t) in enumerate(keys)
        ]
        if edges:
            found = store.execute(
                "UNWIND $edges AS e MATCH (a)-[r]->(b) "
                "WHERE a.id=e.source AND b.id=e.target AND type(r)=e.type "
                "RETURN DISTINCT e.key AS key LIMIT 49",
                {"edges": edges},
            )
            if len(found) != len(edges):
                raise ToolError("AGENT_NATIVE_EDGE_MISMATCH", "Native directed proof failed.")
        count = store.query_count
    context.guard()
    result = NativeToolResult(
        status="PARTIAL_CONTEXT"
        if truncated or context.source.results_may_be_truncated
        else "INSUFFICIENT_EVIDENCE"
        if not context.source.evidence
        else "RETURNED_CONTEXT",
        entity_ids=ids,
        graph_paths=paths,
        records=records,
        comparisons=comparisons,
        gap_codes=sorted(set(gaps))[:20],
        truncated=truncated,
    )
    if len(result.model_dump_json().encode()) > 65536:
        raise ToolError("AGENT_TOOL_OUTPUT_LIMIT", "Native tool output exceeds byte bound.")
    return AgentStep(
        step_number=step_number,
        tool_name=tool_name,
        parameters=arguments,
        subject_ids=list(subject[1]),
        selected_by=selected_by,
        native_query_count=count,
        result=result,
        elapsed_ms=round((time.monotonic() - start) * 1000, 3),
    )
