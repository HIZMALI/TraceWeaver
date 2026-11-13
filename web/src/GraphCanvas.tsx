import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Node,
  type NodeProps,
  type ReactFlowInstance,
} from "@xyflow/react";
import { useEffect, useState } from "react";
import type { Graph } from "./graph";
import { edgeKey } from "./graph";
import type { Path } from "./contracts";

type ProofNode = Node<{ kind: string; name: string; entityId: string }>;
function EntityNode({ data }: NodeProps<ProofNode>) {
  return (
    <div className={`entity-node kind-${data.kind.toLowerCase()}`}>
      {[Position.Left, Position.Right, Position.Top, Position.Bottom].map(
        (position) => (
          <span key={position}>
            <Handle
              id={"target-" + position}
              type="target"
              position={position}
              isConnectable={false}
            />
            <Handle
              id={"source-" + position}
              type="source"
              position={position}
              isConnectable={false}
            />
          </span>
        ),
      )}
      <span className="entity-kind">{data.kind}</span>
      <strong>{data.entityId}</strong>
      {data.name !== data.entityId && (
        <span className="entity-name">{data.name}</span>
      )}
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
  const [instance, setInstance] = useState<ReactFlowInstance<ProofNode> | null>(
    null,
  );
  const selectionKey = paths.map((p) => p.node_ids.join("~")).join("|");
  const [hoveredEdge, setHoveredEdge] = useState("");
  const candidateViewport = graph.nodes.filter((n) => n.kind !== "Evidence");
  useEffect(() => {
    if (!instance || !selectionKey) return;
    const ids = new Set(selectionKey.split(/[~|]/));
    void instance.fitView({
      nodes: graph.nodes
        .filter((n) => ids.has(n.id))
        .map((n) => ({ id: n.id })),
      padding: 0.35,
      maxZoom: 1.25,
      duration: 0,
    });
  }, [instance, selectionKey, graph.nodes]);
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
  const edges = graph.edges.map((e) => {
    const source = graph.nodes.find((n) => n.id === e.source)!,
      target = graph.nodes.find((n) => n.id === e.target)!;
    const horizontal =
      Math.abs(target.x - source.x) >= Math.abs(target.y - source.y);
    const sourceSide = horizontal
      ? target.x > source.x
        ? "right"
        : "left"
      : target.y > source.y
        ? "bottom"
        : "top";
    const targetSide = (
      { right: "left", left: "right", bottom: "top", top: "bottom" } as const
    )[sourceSide];
    return {
      id: e.id,
      source: e.source,
      target: e.target,
      sourceHandle: "source-" + sourceSide,
      targetHandle: "target-" + targetSide,
      label:
        activeEdges.has(e.id) ||
        hoveredEdge === e.id ||
        (!paths.length &&
          graph.nodes.length <= 14 &&
          ["AFFECTS", "DEPENDS_ON", "TARGETS"].includes(e.type))
          ? e.type
          : undefined,
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
      labelStyle: { fill: "#dce7ef", fontSize: 14, fontWeight: 600 },
      labelBgStyle: { fill: "#0f1822", fillOpacity: 0.95 },
      labelBgPadding: [4, 3] as [number, number],
    };
  });
  return (
    <div
      className="graph-canvas"
      aria-label="Returned directed graph"
      data-testid="graph-canvas"
    >
      <p className="graph-view-note">
        Initial viewport favors candidate context. Edge labels appear on
        focus/hover; all stored arrows and counts remain. Fit view shows all
        returned nodes.
      </p>
      {paths.length > 0 && (
        <button
          className="focus-path-button"
          onClick={() =>
            void instance?.fitView({
              nodes: graph.nodes
                .filter((n) => activeNodes.has(n.id))
                .map((n) => ({ id: n.id })),
              padding: 0.35,
              maxZoom: 1.25,
              duration: 0,
            })
          }
        >
          Focus selected paths
        </button>
      )}
      {!graph.nodes.length ? (
        <div className="graph-empty">
          No paths match this view. Adjust visual filters; no relationships are
          invented.
        </div>
      ) : (
        <ReactFlow
          onInit={setInstance}
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          nodesDraggable={false}
          ariaLabelConfig={{
            "node.a11yDescription.default":
              "Read-only node. Use the accessible path list to inspect proof.",
            "node.a11yDescription.keyboardDisabled":
              "Read-only node. Use the accessible path list to inspect proof.",
            "edge.a11yDescription.default":
              "Read-only stored relationship. Use the accessible path list to inspect proof.",
          }}
          nodesConnectable={false}
          edgesReconnectable={false}
          deleteKeyCode={null}
          onNodeClick={(_, n) => onSelect("node:" + n.id)}
          onEdgeClick={(_, e) => onSelect("edge:" + e.id)}
          onEdgeMouseEnter={(_, e) => setHoveredEdge(e.id)}
          onEdgeMouseLeave={() => setHoveredEdge("")}
          fitView
          fitViewOptions={{
            padding: 0.12,
            nodes: candidateViewport.map((n) => ({ id: n.id })),
            maxZoom: 1.15,
          }}
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
