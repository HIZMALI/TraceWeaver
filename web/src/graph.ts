import { allPaths, pathKey, type Bundle, type Path } from "./contracts";

export type Kind =
  "Incident" | "Service" | "Deployment" | "Change" | "Evidence";
export interface GraphNode {
  id: string;
  kind: Kind;
  name: string;
  x: number;
  y: number;
}
export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  reverse: boolean;
}
export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  paths: Path[];
  omittedNodes: number;
  omittedEdges: number;
}
export const edgeKey = (e: {
  type: string;
  source_id: string;
  target_id: string;
}) => JSON.stringify([e.type, e.source_id, e.target_id]);
export const candidateKey = (dep: string, target: string) => `${dep}~${target}`;
export const pairKey = (ids: string[]) => [...ids].sort().join("~");
export const NODE_CAP = 300,
  EDGE_CAP = 600;

export function graphFromBundle(b: Bundle): Graph {
  const i = b.investigation;
  const roles = new Map<string, { kind: Kind; name: string }>();
  function role(id: string, kind: Kind, name = id) {
    if (!kind || i.entity_kinds[id] !== kind)
      throw new Error("Native graph kind mismatch");
    const existing = roles.get(id);
    if (existing && existing.kind !== kind)
      throw new Error("Ambiguous graph identity");
    roles.set(id, { kind, name });
  }
  role(i.incident_id, "Incident", i.title.text);
  i.affected_services.forEach((s) => role(s.id, "Service", s.name.text));
  i.candidates.forEach((c) => {
    role(c.deployment_id, "Deployment", c.name.text);
    if (!roles.has(c.target_service_id)) role(c.target_service_id, "Service");
    c.changes.forEach((x) => role(x.change_id, "Change", x.name.text));
  });
  i.evidence.forEach((e) => {
    role(e.evidence_id, "Evidence");
    e.observed_service_ids.forEach((s) => {
      if (!roles.has(s)) role(s, "Service");
    });
  });
  const rawPaths = [
    ...allPaths(b),
    ...b.explanation.claims.flatMap((c) =>
      c.citations.flatMap((x) => (x.graph_path ? [x.graph_path] : [])),
    ),
  ];
  const paths = [
    ...new Map(rawPaths.map((p) => [pathKey(p), p])).values(),
  ].sort((a, b) => pathKey(a).localeCompare(pathKey(b), "en"));
  const edges = new Map<string, GraphEdge>();
  const included = new Set<string>();
  paths.forEach((p) => {
    p.node_ids.forEach((id) => {
      included.add(id);
      if (!roles.has(id)) role(id, i.entity_kinds[id]);
    });
    p.edges.forEach((e) => {
      const key = edgeKey(e);
      const previous = edges.get(key);
      edges.set(key, {
        id: key,
        source: e.source_id,
        target: e.target_id,
        type: e.type,
        reverse: e.traversal_direction === "REVERSE" || !!previous?.reverse,
      });
    });
  });
  const order: Kind[] = [
    "Incident",
    "Service",
    "Evidence",
    "Deployment",
    "Change",
  ];
  const sorted = [...included].sort(
    (a, b) =>
      order.indexOf(roles.get(a)!.kind) - order.indexOf(roles.get(b)!.kind) ||
      a.localeCompare(b, "en"),
  );
  const rows: Record<Kind, number> = {
    Incident: 0,
    Service: 0,
    Evidence: 0,
    Deployment: 0,
    Change: 0,
  };
  const columns: Record<Kind, number> = {
    Incident: 0,
    Service: 1,
    Evidence: 0,
    Deployment: 2,
    Change: 3,
  };
  const nodes = sorted.slice(0, NODE_CAP).map((id) => {
    const r = roles.get(id)!;
    const row = rows[r.kind]++;
    return {
      id,
      ...r,
      x:
        r.kind === "Evidence"
          ? Math.floor(row / 6) * 220
          : columns[r.kind] * 220,
      y:
        (r.kind === "Evidence" ? 280 : r.kind === "Incident" ? 110 : 0) +
        (r.kind === "Evidence" ? row % 6 : row) *
          (r.kind === "Evidence" ? 94 : 106),
    };
  });
  const allowed = new Set(nodes.map((n) => n.id));
  const all = [...edges.values()].sort((a, b) =>
    a.id.localeCompare(b.id, "en"),
  );
  const visible = all
    .filter((e) => allowed.has(e.source) && allowed.has(e.target))
    .slice(0, EDGE_CAP);
  return {
    nodes,
    edges: visible,
    paths,
    omittedNodes: sorted.length - nodes.length,
    omittedEdges: all.length - visible.length,
  };
}

export interface Filters {
  kind: string;
  edge: string;
  temporal: string;
  assessment: string;
  provenance: string;
}
export const defaultFilters: Filters = {
  kind: "ALL",
  edge: "ALL",
  temporal: "ALL",
  assessment: "ALL",
  provenance: "ALL",
};
export function filterGraph(g: Graph, b: Bundle, f: Filters): Graph {
  const excluded = new Set<string>();
  b.investigation.candidates.forEach((c) => {
    if (
      (f.temporal !== "ALL" && c.temporal_classification !== f.temporal) ||
      (f.assessment !== "ALL" && c.candidate_assessment !== f.assessment)
    )
      excluded.add(c.deployment_id);
  });
  b.investigation.evidence.forEach((e) => {
    if (
      (f.temporal !== "ALL" && e.temporal_classification !== f.temporal) ||
      (f.provenance !== "ALL" && e.provenance_status !== f.provenance)
    )
      excluded.add(e.evidence_id);
  });
  const nodes = g.nodes.filter(
    (n) => (f.kind === "ALL" || n.kind === f.kind) && !excluded.has(n.id),
  );
  const ids = new Set(nodes.map((n) => n.id));
  const edges = g.edges.filter(
    (e) =>
      (f.edge === "ALL" || e.type === f.edge) &&
      ids.has(e.source) &&
      ids.has(e.target),
  );
  return { ...g, nodes, edges };
}

export function selectionPaths(b: Bundle, selection: string): Path[] {
  const index = selection.indexOf(":");
  const kind = selection.slice(0, index),
    id = selection.slice(index + 1);
  if (kind === "claim")
    return (
      b.explanation.claims
        .find((c) => c.claim_id === id)
        ?.citations.flatMap((c) => (c.graph_path ? [c.graph_path] : [])) ?? []
    );
  if (kind === "candidate") {
    const c = b.investigation.candidates.find(
      (c) => candidateKey(c.deployment_id, c.target_service_id) === id,
    );
    return c ? [...c.graph_paths, ...c.changes.map((x) => x.graph_path)] : [];
  }
  if (kind === "evidence")
    return (
      b.investigation.evidence.find((e) => e.evidence_id === id)?.graph_paths ??
      []
    );
  if (kind === "comparison") {
    const c = b.investigation.contradictions.find(
      (c) => pairKey(c.evidence_ids) === id,
    );
    return c
      ? b.investigation.evidence
          .filter((e) => c.evidence_ids.includes(e.evidence_id))
          .flatMap((e) =>
            e.graph_paths.filter((p) => p.node_ids.at(-1) === c.service_id),
          )
      : [];
  }
  if (kind === "node")
    return allPaths(b).filter((p) => p.node_ids.includes(id));
  if (kind === "edge")
    return allPaths(b).filter((p) => p.edges.some((e) => edgeKey(e) === id));
  return [];
}

export function selectionExists(b: Bundle, g: Graph, s: string): boolean {
  if (!s) return true;
  if (s.startsWith("claim:"))
    return b.explanation.claims.some((c) => `claim:${c.claim_id}` === s);
  if (s.startsWith("comparison:"))
    return b.investigation.contradictions.some(
      (c) => `comparison:${pairKey(c.evidence_ids)}` === s,
    );
  return (
    selectionPaths(b, s).length > 0 &&
    (!s.startsWith("node:") || g.nodes.some((n) => `node:${n.id}` === s))
  );
}
