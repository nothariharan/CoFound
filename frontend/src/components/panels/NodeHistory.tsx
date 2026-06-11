import type { GraphNode } from '@/types'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { formatRelativeTime } from '@/utils/formatters'

interface NodeHistoryProps {
  node: GraphNode
}

export function NodeHistory({ node }: NodeHistoryProps) {
  const history = [...(node.research_history ?? [])].reverse()

  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col gap-4 p-4">
        {history.length === 0 && (
          <div className="rounded-lg border border-border bg-background/60 p-3">
            <p className="text-sm font-medium text-foreground">No research attempts yet.</p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Approve research for this node to see attempts, critique scores, evidence, and final status here.
            </p>
          </div>
        )}

        {history.map((entry, index) => (
          <div key={`${entry.task_id ?? entry.task}-${entry.timestamp ?? index}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <Badge variant={variantForStatus(entry.status)}>{labelForStatus(entry.status)}</Badge>
                <p className="mt-2 text-sm font-medium leading-snug text-foreground">{entry.task}</p>
              </div>
              {typeof entry.score === 'number' && (
                <span className="rounded-md border border-border px-2 py-1 text-xs tabular-nums text-muted-foreground">
                  {entry.score}/100
                </span>
              )}
            </div>

            {entry.timestamp && (
              <p className="mt-1 text-xs text-muted-foreground">{formatRelativeTime(entry.timestamp)}</p>
            )}
            {entry.query && <p className="mt-2 text-xs text-muted-foreground">Query: {entry.query}</p>}
            {entry.tools && entry.tools.length > 0 && (
              <p className="mt-1 text-xs text-muted-foreground">Tools: {entry.tools.join(', ')}</p>
            )}
            {entry.reason && <p className="mt-2 text-sm text-muted-foreground">{entry.reason}</p>}
            {entry.result?.summary && (
              <p className="mt-2 text-sm leading-relaxed text-foreground/90">{entry.result.summary}</p>
            )}

            {entry.result?.items && entry.result.items.length > 0 && (
              <div className="mt-3 flex flex-col gap-2">
                {entry.result.items.slice(0, 3).map((item, itemIndex) => (
                  <div key={`${item.url ?? item.title ?? itemIndex}`} className="rounded-md border border-border p-2">
                    <p className="text-xs font-medium text-foreground">{item.title || item.source || 'Evidence'}</p>
                    {item.snippet && <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.snippet}</p>}
                    {item.url && (
                      <a className="mt-1 block truncate text-xs text-primary" href={item.url} target="_blank" rel="noreferrer">
                        {item.url}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}

            {index < history.length - 1 && <Separator className="mt-4" />}
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}

function labelForStatus(status?: string) {
  if (status === 'accepted') return 'Accepted'
  if (status === 'partial') return 'Needs Work'
  if (status === 'failed') return 'Failed'
  if (status === 'running') return 'Running'
  return 'Research'
}

function variantForStatus(status?: string): 'success' | 'warning' | 'destructive' | 'outline' {
  if (status === 'accepted') return 'success'
  if (status === 'partial' || status === 'running') return 'warning'
  if (status === 'failed') return 'destructive'
  return 'outline'
}
