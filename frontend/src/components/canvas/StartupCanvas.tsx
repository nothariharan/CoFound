import { useCallback, useEffect, useRef, useState } from 'react'
import { Plus } from 'lucide-react'
import {
  ReactFlow,
  Background,
  Controls,
  useEdgesState,
  useNodesState,
  type Node,
  type Edge,
} from '@xyflow/react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { NodeCard, type NodeCardData } from '@/components/canvas/NodeCard'
import { CustomTaskDialog } from '@/components/canvas/CustomTaskDialog'
import { NODE_EDGES, buildDynamicEdges, getNodePosition, layoutCustomResearchNodes } from '@/utils/canvasLayout'
import { useCanvasUnlockAnimation } from '@/hooks/useAnimations'
import { Button } from '@/components/ui/button'
import type { Workspace } from '@/types'
import { getNodeTypeColor } from '@/utils/nodeColors'

const nodeTypes = { nodeCard: NodeCard }

function buildFlowNodes(
  workspace: Workspace,
  selectedNodeId: string | null,
  onSelect: (id: string) => void,
  existingNodes: Node[],
): Node[] {
  const positionById = new Map(existingNodes.map((node) => [node.id, node.position]))
  const customPositions = layoutCustomResearchNodes(workspace)

  return workspace.nodes.map((node) => ({
    id: node.node_id,
    type: 'nodeCard',
    position:
      positionById.get(node.node_id) ??
      customPositions.get(node.node_id) ??
      getNodePosition(node.node_id, node.type),
    draggable: true,
    data: {
      node,
      onSelect,
      selected: node.node_id === selectedNodeId,
    } satisfies NodeCardData,
  }))
}

function buildFlowEdges(workspace: Workspace): Edge[] {
  const nodeIds = new Set(workspace.nodes.map((node) => node.node_id))
  const nodeById = new Map(workspace.nodes.map((node) => [node.node_id, node]))

  const staticEdges = NODE_EDGES.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
  const dynamicEdges = buildDynamicEdges(workspace).filter(
    (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target),
  )
  const allEdges = [...staticEdges, ...dynamicEdges]

  return allEdges.map((edge) => {
    const sourceNode = nodeById.get(edge.source)
    const targetNode = nodeById.get(edge.target)
    const activeNode =
      targetNode?.active_agents.length
        ? targetNode
        : sourceNode?.active_agents.length
          ? sourceNode
          : null
    const isActive = Boolean(activeNode)

    return {
      id: `e-${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      animated: isActive,
      className: isActive ? 'edge-agent-active' : undefined,
      style: {
        stroke: isActive ? getNodeTypeColor(activeNode!.type) : 'var(--border)',
        strokeWidth: isActive ? 2.5 : 1,
        opacity: isActive ? 1 : 0.45,
      },
    }
  })
}

export function StartupCanvas() {
  const { workspace, selectedNodeId, setSelectedNodeId } = useWorkspaceStore()
  const prevUnlockedRef = useRef<Set<string>>(new Set())
  const [newlyUnlocked, setNewlyUnlocked] = useState<string[]>([])
  const [customTaskOpen, setCustomTaskOpen] = useState(false)

  useEffect(() => {
    if (!workspace) {
      prevUnlockedRef.current = new Set()
      return
    }

    const currentUnlocked = new Set(
      workspace.nodes
        .filter((n) => n.status !== 'locked' && n.type !== 'core_idea')
        .map((n) => n.node_id),
    )

    const fresh = [...currentUnlocked].filter((id) => !prevUnlockedRef.current.has(id))
    prevUnlockedRef.current = currentUnlocked
    if (fresh.length) setNewlyUnlocked(fresh)
  }, [workspace])

  const canvasRef = useCanvasUnlockAnimation(newlyUnlocked)

  const onSelect = useCallback(
    (id: string) => setSelectedNodeId(id),
    [setSelectedNodeId],
  )

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const lastWorkspaceIdRef = useRef<string | null>(null)

  useEffect(() => {
    if (!workspace) {
      lastWorkspaceIdRef.current = null
      setNodes([])
      setEdges([])
      return
    }

    const workspaceChanged = lastWorkspaceIdRef.current !== workspace.idea_id
    lastWorkspaceIdRef.current = workspace.idea_id

    setNodes((current) =>
      buildFlowNodes(workspace, selectedNodeId, onSelect, workspaceChanged ? [] : current),
    )
    setEdges(buildFlowEdges(workspace))
  }, [workspace, selectedNodeId, onSelect, setNodes, setEdges])

  return (
    <div ref={canvasRef} className="relative size-full min-h-0 bg-background">
      {workspace && (
        <div className="absolute left-5 top-5 z-10 max-w-sm">
          <p className="line-clamp-2 text-sm leading-relaxed text-muted-foreground">
            {workspace.nodes.find((n) => n.type === 'core_idea')?.summary ?? workspace.workspace_name}
          </p>
          <p className="mt-1.5 text-[11px] tabular-nums text-muted-foreground/80">
            Idea confidence{' '}
            <span className="font-medium text-foreground/80">
              {workspace.nodes.find((n) => n.type === 'core_idea')?.confidence ?? 0}%
            </span>
          </p>
        </div>
      )}

      {workspace && (
        <div className="absolute right-6 top-6 z-10">
          <Button
            type="button"
            size="icon"
            className="size-11 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90"
            aria-label="Spawn custom agent"
            onClick={() => setCustomTaskOpen(true)}
          >
            <Plus className="size-5" />
          </Button>
        </div>
      )}

      <CustomTaskDialog open={customTaskOpen} onOpenChange={setCustomTaskOpen} />

      <ReactFlow
        className="size-full"
        style={{ width: '100%', height: '100%' }}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.4}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
        nodesDraggable
        nodesConnectable={false}
        panOnScroll
        nodeDragThreshold={6}
      >
        <Background color="var(--border)" gap={24} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}
