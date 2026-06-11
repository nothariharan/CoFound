import { useEffect, useRef } from 'react'
import { useSSEFeed } from '@/hooks/useSSEFeed'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

export function AgentFeed() {
  const workspace = useWorkspaceStore((s) => s.workspace)
  const { fetchWorkspace } = useWorkspace()
  const { messages, connected } = useSSEFeed(workspace?.idea_id)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!workspace?.idea_id) return
    const last = messages.at(-1)
    if (last?.type === 'done' || last?.type === 'critique') {
      void fetchWorkspace(workspace.idea_id)
    }
  }, [messages, workspace?.idea_id, fetchWorkspace])

  useEffect(() => {
    if (!workspace?.idea_id || !connected) return
    const hasActiveAgents = workspace.nodes.some((node) => node.active_agents.length > 0)
    const interval = window.setInterval(() => {
      void fetchWorkspace(workspace.idea_id)
    }, hasActiveAgents ? 3000 : 8000)
    return () => window.clearInterval(interval)
  }, [workspace?.idea_id, workspace?.nodes, connected, fetchWorkspace])

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Agent Feed</span>
        <span
          className={cn('size-1.5 rounded-full', connected ? 'bg-status-validated' : 'bg-muted-foreground')}
          aria-label={connected ? 'Connected' : 'Disconnected'}
        />
      </div>
      <ScrollArea className="flex-1">
        <div className="bg-background p-4 font-mono text-xs leading-relaxed text-foreground/90">
          {messages.length === 0 && (
            <p className="text-muted-foreground">Waiting for agent activity...</p>
          )}
          {messages.map((msg, i) => (
            <p
              key={i}
              className={cn(
                'mb-1',
                msg.type === 'critique' && 'text-status-needs-work',
                msg.type === 'error' && 'text-destructive',
                msg.type === 'done' && 'text-status-validated',
              )}
            >
              {msg.text}
            </p>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
    </div>
  )
}
