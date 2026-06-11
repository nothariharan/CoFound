import { formatConfidence, formatRelativeTime } from '@/utils/formatters'
import { statusBadgeVariant, statusLabels } from '@/utils/nodeColors'
import type { GraphNode } from '@/types'
import { SourcePills } from '@/components/canvas/SourcePills'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

interface NodeDetailsProps {
  node: GraphNode
}

export function NodeDetails({ node }: NodeDetailsProps) {
  const latest = node.research_history?.at(-1)
  const latestItems = latest?.result?.items ?? []

  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-foreground">{node.title}</h3>
            <Badge variant={statusBadgeVariant[node.status]} className="mt-1">
              {statusLabels[node.status]}
            </Badge>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Confidence</span>
            <span className="font-medium tabular-nums text-foreground">{formatConfidence(node.confidence)}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${node.confidence}%` }}
            />
          </div>
        </div>

        <div className="flex gap-4 text-xs">
          <div>
            <p className="text-muted-foreground">Last updated</p>
            <p className="text-foreground">{formatRelativeTime(node.last_updated)}</p>
          </div>
          {node.active_agents.length > 0 && (
            <div>
              <p className="text-muted-foreground">Agent</p>
              <p className="text-foreground">{node.active_agents[0]?.replace('researcher_', 'R') ?? '—'}</p>
            </div>
          )}
        </div>

        <Separator />

        {(node.overview || node.summary) && (
          <div>
            <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Overview</p>
            <p className="text-sm leading-relaxed text-foreground/90">{node.overview ?? node.summary}</p>
          </div>
        )}

        {node.pain_points && node.pain_points.length > 0 && (
          <div>
            <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Top pain points</p>
            <div className="flex flex-col gap-2">
              {node.pain_points.map((pp) => (
                <div key={pp.label} className="flex items-center justify-between gap-3">
                  <span className="text-sm text-foreground/90">{pp.label}</span>
                  <span className="shrink-0 text-xs tabular-nums text-muted-foreground">{pp.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {node.agent_notes && (
          <div>
            <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Agent Notes</p>
            <p className="text-sm text-muted-foreground">{node.agent_notes}</p>
          </div>
        )}

        {node.source_pills.length > 0 && (
          <div>
            <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Sources</p>
            <SourcePills pills={node.source_pills} />
          </div>
        )}

        {node.source_pills.length === 0 && (
          <div>
            <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Sources</p>
            <p className="text-sm text-muted-foreground">
              {latest
                ? 'No accepted source pills yet. Check the latest research attempt below for raw evidence and critique.'
                : 'No research has been approved for this node yet.'}
            </p>
          </div>
        )}

        {latest && (
          <div>
            <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Latest Attempt</p>
            <p className="text-sm text-foreground/90">
              {latest.status ?? 'research'} {typeof latest.score === 'number' ? `(${latest.score}/100)` : ''}
            </p>
            {latest.reason && <p className="mt-1 text-sm text-muted-foreground">{latest.reason}</p>}
            {latestItems.length > 0 && (
              <div className="mt-3 flex flex-col gap-2">
                {latestItems.slice(0, 3).map((item, index) => (
                  <div key={`${item.url ?? item.title ?? index}`} className="rounded-md border border-border p-2">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{sourceLabel(item)}</p>
                    <p className="mt-1 text-xs font-medium text-foreground">{item.title || 'Evidence'}</p>
                    {item.snippet && <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.snippet}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </ScrollArea>
  )
}

function sourceLabel(item: { source?: string; origin?: string }) {
  if (item.source === 'web' || item.origin === 'web') return 'Web'
  if (item.origin === 'reddit') return 'Reddit'
  if (item.source === 'scrapling') return 'Web'
  return item.source || 'Evidence'
}
