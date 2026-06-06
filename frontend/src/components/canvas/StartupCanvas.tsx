import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
} from '@xyflow/react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { NodeCard, type NodeCardData } from '@/components/canvas/NodeCard'
import { NODE_EDGES, getNodePosition } from '@/utils/canvasLayout'
import { useCanvasUnlockAnimation } from '@/hooks/useAnimations'

const nodeTypes = { nodeCard: NodeCard }

export function StartupCanvas() {
  const { workspace, selectedNodeId, setSelectedNodeId, demoStage } = useWorkspaceStore()
  const canvasRef = useCanvasUnlockAnimation(
    demoStage >= 2 ? ['node-audience', 'node-market', 'node-competitors'] : [],
  )

  const onSelect = useCallback(
    (id: string) => setSelectedNodeId(id),
    [setSelectedNodeId],
  )

  const { nodes, edges } = useMemo(() => {
    if (!workspace) return { nodes: [], edges: [] as Edge[] }

    const nodeIds = new Set(workspace.nodes.map((n) => n.node_id))

    const flowNodes: Node[] = workspace.nodes.map((node) => {
      const pos = getNodePosition(node.node_id, node.type)
      return {
        id: node.node_id,
        type: 'nodeCard',
        position: pos,
        data: {
          node,
          onSelect,
          selected: node.node_id === selectedNodeId,
        } satisfies NodeCardData,
      }
    })

    const flowEdges: Edge[] = NODE_EDGES.filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target),
    ).map((edge) => ({
      id: `e-${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      style: { stroke: 'var(--border)', strokeWidth: 1 },
      animated: workspace.nodes.find((n) => n.node_id === edge.target)?.active_agents.length ? true : false,
    }))

    return { nodes: flowNodes, edges: flowEdges }
  }, [workspace, selectedNodeId, onSelect])

  return (
    <div ref={canvasRef} className="relative size-full min-h-0 bg-background">
      {workspace && (
        <div className="absolute left-6 top-6 z-10 max-w-md">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{workspace.workspace_name}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {workspace.nodes.find((n) => n.type === 'core_idea')?.summary ?? 'AI copilot for busy restaurant owners'}
          </p>
          <div className="mt-2 inline-flex items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground">
            Idea confidence{' '}
            <span className="font-medium tabular-nums text-foreground">
              {workspace.nodes.find((n) => n.type === 'core_idea')?.confidence ?? 0}%
            </span>
          </div>
        </div>
      )}

      <ReactFlow
        className="size-full"
        style={{ width: '100%', height: '100%' }}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.4}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        panOnScroll
      >
        <Background color="var(--border)" gap={24} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}
