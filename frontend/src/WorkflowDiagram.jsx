import React, { useMemo, useEffect, useState } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 150;
const nodeHeight = 50;

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

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
  return (
    <div className="react-flow__node-custom">
      <div style={{ fontWeight: 'bold' }}>{data.label}</div>
      {data.group && data.group !== 'root' && (
        <div style={{ fontSize: '10px', color: 'var(--color-cyan)', marginTop: '4px' }}>
          {data.group}
        </div>
      )}
    </div>
  );
};

const ExternalNode = ({ data }) => {
  return (
    <div className="react-flow__node-external">
      <div style={{ fontWeight: 'bold' }}>{data.label}</div>
      <div style={{ fontSize: '10px', color: 'var(--color-magenta)', marginTop: '4px' }}>
        External
      </div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
  external: ExternalNode,
};

const WorkflowDiagram = ({ diagramData }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (diagramData && diagramData.nodes && diagramData.edges) {
      const initialNodes = diagramData.nodes.map((n) => ({
        id: n.id,
        type: n.type === 'external' ? 'external' : 'custom',
        data: { label: n.label, group: n.group },
        position: { x: 0, y: 0 },
      }));

      const initialEdges = diagramData.edges.map((e, idx) => ({
        id: `e-${e.source}-${e.target}-${idx}`,
        source: e.source,
        target: e.target,
        animated: true,
        style: { stroke: 'var(--color-magenta)', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'var(--color-magenta)',
        },
      }));

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        initialNodes,
        initialEdges
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
  }, [diagramData, setNodes, setEdges]);

  return (
    <div className="diagram-panel">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
      >
        <Controls style={{ button: { backgroundColor: 'var(--color-bg)', color: 'var(--color-cyan)', border: '1px solid var(--color-cyan)' } }} />
        <Background color="var(--color-cyan)" gap={16} size={1} />
      </ReactFlow>
    </div>
  );
};

export default WorkflowDiagram;
