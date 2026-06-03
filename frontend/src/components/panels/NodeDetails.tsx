import { formatConfidence, formatNodeType, formatRelativeTime } from '../../utils/formatters'
import { statusLabels } from '../../utils/nodeColors'
import type { GraphNode } from '../../types'
import { SourcePills } from '../canvas/SourcePills'

interface NodeDetailsProps {
  node: GraphNode
}

export function NodeDetails({ node }: NodeDetailsProps) {
  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="border-b border-[#e5e5e5] px-4 py-3">
        <h3 className="text-sm font-semibold text-[#171717]">{node.title}</h3>
        <p className="text-xs text-[#737373]">{formatNodeType(node.type)}</p>
      </div>
      <div className="space-y-4 p-4">
        <div>
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
            Summary
          </p>
          <p className="text-sm text-[#171717]">{node.summary}</p>
        </div>
        <div className="flex gap-6">
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
              Confidence
            </p>
            <p className="text-sm font-medium text-[#171717]">
              {formatConfidence(node.confidence)}
            </p>
          </div>
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
              Status
            </p>
            <p className="text-sm text-[#171717]">{statusLabels[node.status]}</p>
          </div>
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
              Updated
            </p>
            <p className="text-sm text-[#171717]">
              {formatRelativeTime(node.last_updated)}
            </p>
          </div>
        </div>
        {node.agent_notes && (
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
              Agent Notes
            </p>
            <p className="text-sm text-[#737373]">{node.agent_notes}</p>
          </div>
        )}
        {node.source_pills.length > 0 && (
          <div>
            <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
              Sources
            </p>
            <SourcePills pills={node.source_pills} />
          </div>
        )}
      </div>
    </div>
  )
}
