import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
} from '@xyflow/react'
import { useWorkspaceStore } from '../../store/workspaceStore'
import { NodeCard, type NodeCardData } from './NodeCard'

const nodeTypes = { nodeCard: NodeCard }

export function StartupCanvas() {
  const { workspace, selectedNodeId, setSelectedNodeId } = useWorkspaceStore()

  const onSelect = useCallback(
    (id: string) => setSelectedNodeId(id),
    [setSelectedNodeId],
  )

  const { nodes, edges } = useMemo(() => {
    if (!workspace) return { nodes: [], edges: [] as Edge[] }

    const flowNodes: Node[] = workspace.nodes.map((node, i) => ({
      id: node.node_id,
      type: 'nodeCard',
      position: { x: 280, y: i * 180 + 40 },
      data: {
        node,
        onSelect,
        selected: node.node_id === selectedNodeId,
      } satisfies NodeCardData,
    }))

    const flowEdges: Edge[] = workspace.nodes.slice(1).map((node, i) => ({
      id: `e-${workspace.nodes[i].node_id}-${node.node_id}`,
      source: workspace.nodes[i].node_id,
      target: node.node_id,
      style: { stroke: '#e5e5e5', strokeWidth: 1 },
    }))

    return { nodes: flowNodes, edges: flowEdges }
  }, [workspace, selectedNodeId, onSelect])

  return (
    <div className="h-full w-full bg-[#fafafa]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.5}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#e5e5e5" gap={24} size={1} />
        <Controls showInteractive={false} className="!border-[#e5e5e5] !shadow-none" />
      </ReactFlow>
    </div>
  )
}
