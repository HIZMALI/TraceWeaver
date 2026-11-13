import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import type { Graph } from "./graph";
import { edgeKey } from "./graph";
import type { Path } from "./contracts";

type ProofNode = Node<{ kind: string; name: string; entityId: string }>;
function EntityNode({ data }: NodeProps<ProofNode>) {
  return (
    <div className={`entity-node kind-${data.kind.toLowerCase()}`}>
      <Handle type="target" position={Position.Left} isConnectable={false} />
      <span className="entity-kind">{data.kind}</span>
      <strong>{data.entityId}</strong>
      {data.name !== data.entityId && (
        <span className="entity-name">{data.name}</span>
      )}
      <Handle type="source" position={Position.Right} isConnectable={false} />
    </div>
  );
}
const nodeTypes = { entity: EntityNode };
export function GraphCanvas({
  graph,
  paths,
  onSelect,
}: {
  graph: Graph;
  paths: Path[];
  onSelect: (s: string) => void;
}) {
  const activeNodes = new Set(paths.flatMap((p) => p.node_ids)),
    activeEdges = new Set(paths.flatMap((p) => p.edges.map(edgeKey)));
  const nodes: ProofNode[] = graph.nodes.map((n) => ({
    id: n.id,
    type: "entity",
    position: { x: n.x, y: n.y },
    data: { kind: n.kind, name: n.name, entityId: n.id },
    ariaLabel: `${n.kind} ${n.id}`,
    style: { opacity: activeNodes.size && !activeNodes.has(n.id) ? 0.22 : 1 },
    selected: activeNodes.has(n.id),
  }));
  const edges = graph.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.type,
    ariaLabel: `${e.type} stored ${e.source} to ${e.target}${e.reverse ? ", traversed in reverse" : ""}`,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 16,
      height: 16,
      color: activeEdges.has(e.id) ? "#6de2cc" : "#70869a",
    },
    style: {
      stroke: activeEdges.has(e.id) ? "#6de2cc" : "#70869a",
      strokeWidth: activeEdges.has(e.id) ? 2.5 : 1.3,
      opacity: activeEdges.size && !activeEdges.has(e.id) ? 0.18 : 1,
    },
    labelStyle: { fill: "#b9c9d7", fontSize: 9, fontWeight: 600 },
    labelBgStyle: { fill: "#0f1822", fillOpacity: 0.95 },
    labelBgPadding: [4, 3] as [number, number],
  }));
  return (
    <div
      className="graph-canvas"
      aria-label="Returned directed graph"
      data-testid="graph-canvas"
    >
      {!graph.nodes.length ? (
        <div className="graph-empty">
          No paths match this view. Adjust visual filters; no relationships are
          invented.
        </div>
      ) : (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          nodesDraggable={false}
          nodesConnectable={false}
          edgesReconnectable={false}
          deleteKeyCode={null}
          onNodeClick={(_, n) => onSelect("node:" + n.id)}
          onEdgeClick={(_, e) => onSelect("edge:" + e.id)}
          fitView
          fitViewOptions={{ padding: 0.18 }}
          minZoom={0.15}
          maxZoom={2.5}
          colorMode="dark"
          proOptions={{ hideAttribution: true }}
          aria-label="Read-only connected graph"
        >
          <Background color="#22303e" gap={20} size={1} />
          <Controls showInteractive={false} />
        </ReactFlow>
      )}
    </div>
  );
}
