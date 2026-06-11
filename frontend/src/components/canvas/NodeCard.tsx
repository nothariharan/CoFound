import { memo, useEffect, useRef } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import {
  BarChart3,
  Building2,
  Code2,
  Eye,
  Lightbulb,
  Lock,
  Rocket,
  Search,
  Target,
  TrendingUp,
  Users,
  Wallet,
} from 'lucide-react'
import { getNodeAgentConfig } from '@/config/nodeAgents'
import type { GraphNode, NodeType } from '@/types'
import { ConfidenceRing } from '@/components/canvas/ConfidenceRing'
import { SourcePills } from '@/components/canvas/SourcePills'
import { AgentChip } from '@/components/canvas/AgentChip'
import { LockOverlay } from '@/components/canvas/LockOverlay'
import { getNodeTypeColor, getStatusTextClass, statusLabels } from '@/utils/nodeColors'
import { formatRelativeTime } from '@/utils/formatters'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { cn } from '@/lib/utils'

export type NodeCardData = {
  node: GraphNode
  onSelect: (id: string) => void
  selected: boolean
}

const nodeIcons: Record<
  NodeType,
  React.ComponentType<{ className?: string; style?: React.CSSProperties }>
> = {
  core_idea: Lightbulb,
  audience: Users,
  market_intelligence: BarChart3,
  competitors: Building2,
  revenue: Wallet,
  product_vision: Target,
  tech_stack: Code2,
  build: Code2,
  launch: Rocket,
  observe: Eye,
  growth: TrendingUp,
  custom_research: Search,
}

function NodeCardComponent({ data }: NodeProps & { data: NodeCardData }) {
  const { node, onSelect, selected } = data
  const isLocked = node.status === 'locked'
  const { pivotBlurredNodes } = useWorkspaceStore()
  const isPivotBlurred = pivotBlurredNodes.includes(node.node_id)
  const cardRef = useRef<HTMLDivElement>(null)

  const Icon = nodeIcons[node.type] ?? Lightbulb
  const typeColor = getNodeTypeColor(node.type)

  useEffect(() => {
    if (isPivotBlurred && cardRef.current) {
      cardRef.current.classList.add('node-pivot-blur')
    } else if (cardRef.current) {
      cardRef.current.classList.remove('node-pivot-blur')
    }
  }, [isPivotBlurred])

  return (
    <div
      ref={cardRef}
      data-node-id={node.node_id}
      onClick={() => !isLocked && onSelect(node.node_id)}
      style={!isLocked ? { borderLeft: `2px solid ${typeColor}` } : undefined}
      className={cn(
        'relative w-[240px] cursor-grab rounded-lg border bg-card p-3.5 transition-colors active:cursor-grabbing',
        selected ? 'border-primary ring-1 ring-primary/30' : 'border-border hover:border-muted-foreground/40',
        isLocked && 'cursor-grab opacity-60',
      )}
    >
      <Handle type="target" position={Position.Top} className="!size-2 !border-border !bg-border" />
      <Handle type="source" position={Position.Bottom} className="!size-2 !border-border !bg-border" />

      {node.active_agents.length > 0 && (
        <AgentChip key={node.node_id} label={getNodeAgentConfig(node.type).name} active />
      )}

      <div className="mb-2.5 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon
            className={cn('size-3.5', isLocked && 'text-muted-foreground')}
            style={!isLocked ? { color: typeColor } : undefined}
          />
          <span className="text-xs font-medium text-foreground">{node.title}</span>
        </div>
        {!isLocked && <ConfidenceRing confidence={node.confidence} status={node.status} />}
        {isLocked && <Lock className="size-4 text-status-locked" />}
      </div>

      <p className="mb-2.5 line-clamp-2 text-[13px] text-foreground">{node.summary}</p>

      <div className="mb-2 flex items-center justify-between">
        <span
          className={cn(
            'text-[10px] font-medium uppercase tracking-wide',
            getStatusTextClass(node.status),
          )}
        >
          {statusLabels[node.status]}
        </span>
        {!isLocked && (
          <span className="text-[10px] text-muted-foreground">{formatRelativeTime(node.last_updated)}</span>
        )}
      </div>

      {!isLocked && <SourcePills pills={node.source_pills} />}

      {isLocked && <LockOverlay />}
    </div>
  )
}

export const NodeCard = memo(NodeCardComponent)
