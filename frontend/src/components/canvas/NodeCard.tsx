import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Lightbulb } from 'lucide-react'
import type { GraphNode } from '../../types'
import { ConfidenceRing } from './ConfidenceRing'
import { SourcePills } from './SourcePills'
import { AgentChip } from './AgentChip'
import { LockOverlay } from './LockOverlay'
import { statusLabels } from '../../utils/nodeColors'
import { formatRelativeTime } from '../../utils/formatters'

export type NodeCardData = {
  node: GraphNode
  onSelect: (id: string) => void
  selected: boolean
}

function NodeCardComponent({ data }: NodeProps & { data: NodeCardData }) {
  const { node, onSelect, selected } = data
  const isLocked = node.status === 'locked'

  return (
    <div
      onClick={() => !isLocked && onSelect(node.node_id)}
      className={`relative w-[240px] cursor-pointer rounded border bg-white p-4 transition-colors ${
        selected ? 'border-[#2563eb]' : 'border-[#e5e5e5] hover:border-[#d4d4d4]'
      } ${isLocked ? 'cursor-default opacity-60' : ''}`}
    >
      <Handle type="target" position={Position.Top} className="!bg-[#e5e5e5]" />
      <Handle type="source" position={Position.Bottom} className="!bg-[#e5e5e5]" />

      {node.active_agents.map((agent) => (
        <AgentChip key={agent} label={agent.slice(0, 1).toUpperCase()} />
      ))}

      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Lightbulb size={14} strokeWidth={1.5} className="text-[#737373]" />
          <span className="text-xs font-medium text-[#737373]">{node.title}</span>
        </div>
        <ConfidenceRing confidence={node.confidence} status={node.status} />
      </div>

      <p className="mb-3 line-clamp-2 text-sm text-[#171717]">{node.summary}</p>

      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[#737373]">
          {statusLabels[node.status]}
        </span>
        <span className="text-[10px] text-[#a3a3a3]">
          {formatRelativeTime(node.last_updated)}
        </span>
      </div>

      <SourcePills pills={node.source_pills} />

      {isLocked && <LockOverlay />}
    </div>
  )
}

export const NodeCard = memo(NodeCardComponent)
