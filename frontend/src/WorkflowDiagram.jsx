import React, { useEffect, useState } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import { FileCode, Package } from 'lucide-react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

const nodeWidth = 172;
const nodeHeight = 60;

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction, nodesep: 60, ranksep: 80 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const newNode = {
      ...node,
      targetPosition: isHorizontal ? 'left' : 'top',
      sourcePosition: isHorizontal ? 'right' : 'bottom',
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };

    return newNode;
  });

  return { nodes: newNodes, edges };
};

const CustomNode = ({ data }) => {
  const targetPos = data.targetPosition === 'left' ? Position.Left : Position.Top;
  const sourcePos = data.sourcePosition === 'right' ? Position.Right : Position.Bottom;
  return (
    <div className="react-flow__node-custom">
      <Handle type="target" position={targetPos} style={{ background: 'var(--color-cyan)', border: 'none', width: 6, height: 6 }} />
      <div style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
        <FileCode size={14} color="var(--color-cyan)" />
        {data.label}
      </div>
      {data.group && data.group !== 'root' && (
        <div style={{ fontSize: '10px', color: 'var(--color-cyan)', marginTop: '4px' }}>
          {data.group}
        </div>
      )}
      <Handle type="source" position={sourcePos} style={{ background: 'var(--color-cyan)', border: 'none', width: 6, height: 6 }} />
    </div>
  );
};

const ExternalNode = ({ data }) => {
  const targetPos = data.targetPosition === 'left' ? Position.Left : Position.Top;
  const sourcePos = data.sourcePosition === 'right' ? Position.Right : Position.Bottom;
  return (
    <div className="react-flow__node-external">
      <Handle type="target" position={targetPos} style={{ background: 'var(--color-magenta)', border: 'none', width: 6, height: 6 }} />
      <div style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
        <Package size={14} color="var(--color-magenta)" />
        {data.label}
      </div>
      <div style={{ fontSize: '10px', color: 'var(--color-magenta)', marginTop: '4px' }}>
        External
      </div>
      <Handle type="source" position={sourcePos} style={{ background: 'var(--color-magenta)', border: 'none', width: 6, height: 6 }} />
    </div>
  );
};

const EntrypointNode = ({ data }) => {
  const targetPos = data.targetPosition === 'left' ? Position.Left : Position.Top;
  const sourcePos = data.sourcePosition === 'right' ? Position.Right : Position.Bottom;
  return (
    <div className="react-flow__node-entrypoint">
      <Handle type="target" position={targetPos} style={{ background: '#39ff14', border: 'none', width: 6, height: 6 }} />
      <div style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
        {data.label}
      </div>
      {data.group && data.group !== 'root' && (
        <div style={{ fontSize: '10px', color: '#39ff14', marginTop: '4px' }}>
          {data.group}
        </div>
      )}
      <Handle type="source" position={sourcePos} style={{ background: '#39ff14', border: 'none', width: 6, height: 6 }} />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
  external: ExternalNode,
  entrypoint: EntrypointNode,
};

const WorkflowDiagram = ({ diagramData }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [layoutDirection, setLayoutDirection] = useState('LR');

  useEffect(() => {
    if (diagramData && diagramData.nodes && diagramData.edges) {
      const isHorizontal = layoutDirection === 'LR';
      const nodeTypeMap = { external: 'external', entrypoint: 'entrypoint', package: 'custom', file: 'custom' };
      const initialNodes = diagramData.nodes.map((n) => ({
        id: n.id,
        type: nodeTypeMap[n.type] || 'custom',
        data: {
          label: n.label,
          group: n.group,
          targetPosition: isHorizontal ? 'left' : 'top',
          sourcePosition: isHorizontal ? 'right' : 'bottom',
        },
        position: { x: 0, y: 0 },
      }));

      // Build a set of valid node IDs to filter out orphan edges
      const nodeIdSet = new Set(initialNodes.map((n) => n.id));

      // Only keep edges where both source and target exist
      const validEdges = diagramData.edges.filter(
        (e) => nodeIdSet.has(e.source) && nodeIdSet.has(e.target)
      );

      const initialEdges = validEdges.map((e, idx) => {
        const isExternal = e.label === 'uses';
        const color = isExternal ? '#ff003c' : '#00f0ff';
        return {
          id: `e-${e.source}-${e.target}-${idx}`,
          source: e.source,
          target: e.target,
          type: 'smoothstep',
          label: e.label,
          labelStyle: { fill: color, fontWeight: 'bold', fontSize: 10 },
          labelBgStyle: { fill: '#141414', fillOpacity: 0.9 },
          labelBgPadding: [4, 2],
          animated: isExternal,
          style: { stroke: color, strokeWidth: isExternal ? 1.5 : 2 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: color,
            width: 16,
            height: 16,
          },
        };
      });

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        initialNodes,
        initialEdges,
        layoutDirection
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
  }, [diagramData, layoutDirection, setNodes, setEdges]);

  const onLayoutToggle = () => {
    setLayoutDirection((prev) => (prev === 'TB' ? 'LR' : 'TB'));
  };

  const nodeCount = nodes.length;
  const edgeCount = edges.length;

  return (
    <div className="diagram-panel">
      <div className="diagram-toolbar">
        <div className="diagram-stats">
          <span className="diagram-stat"><span style={{ color: '#00f0ff' }}>{nodeCount}</span> nodes</span>
          <span className="diagram-stat"><span style={{ color: '#ff003c' }}>{edgeCount}</span> edges</span>
        </div>
        <button
          className="search-btn glitch-hover"
          style={{ padding: '5px 10px', fontSize: '11px' }}
          onClick={onLayoutToggle}
        >
          {layoutDirection === 'TB' ? '↕ VERTICAL' : '↔ HORIZONTAL'}
        </button>
      </div>
      <div className="diagram-legend">
        <span className="legend-item"><span style={{ display: 'inline-block', width: 10, height: 10, border: '1px solid #00f0ff', background: 'rgba(20,20,30,0.9)', marginRight: 4 }}></span> Project File</span>
        <span className="legend-item"><span style={{ display: 'inline-block', width: 10, height: 10, border: '1px dashed #ff003c', background: 'rgba(30,15,20,0.9)', marginRight: 4 }}></span> External Dep</span>
        <span className="legend-item"><span style={{ display: 'inline-block', width: 16, height: 2, background: '#00f0ff', marginRight: 4, verticalAlign: 'middle' }}></span> imports</span>
        <span className="legend-item"><span style={{ display: 'inline-block', width: 16, height: 2, background: '#ff003c', marginRight: 4, verticalAlign: 'middle' }}></span> uses</span>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        attributionPosition="bottom-right"
      >
        <Controls />
        <Background color="#222" gap={20} size={1} />
      </ReactFlow>
    </div>
  );
};

export default WorkflowDiagram;
