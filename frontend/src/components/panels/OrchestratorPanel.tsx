import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowUp, Mic, MicOff } from 'lucide-react'
import { resolveAgentDisplayName } from '@/config/nodeAgents'
import type { GraphNode } from '@/types'
import { useVoiceOrchestrator } from '@/hooks/useVoiceOrchestrator'
import { useSSEFeed } from '@/hooks/useSSEFeed'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { statusBadgeVariant, statusLabels } from '@/utils/nodeColors'
import { cn } from '@/lib/utils'

function getLatestActivity(node: GraphNode): string {
  const latest = node.research_history.at(-1)
  if (node.active_agents.length > 0) {
    return latest?.query || latest?.task || node.agent_notes || 'Research in progress'
  }
  if (latest?.status === 'accepted') {
    return latest.result?.summary || latest.reason || 'Research accepted'
  }
  if (latest?.status === 'failed') {
    return latest.reason || 'Research failed'
  }
  return node.agent_notes || node.summary || 'No activity yet'
}

function ActivityCards() {
  const workspace = useWorkspaceStore((s) => s.workspace)
  const { messages, connected } = useSSEFeed(workspace?.idea_id)
  const { fetchWorkspace } = useWorkspace()
  const bottomRef = useRef<HTMLDivElement>(null)

  const activeNodes = useMemo(
    () => (workspace?.nodes ?? []).filter((node) => node.active_agents.length > 0),
    [workspace?.nodes],
  )

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeNodes.length])

  useEffect(() => {
    if (!workspace?.idea_id) return
    const last = messages.at(-1)
    if (last?.type === 'done' || last?.type === 'critique') {
      void fetchWorkspace(workspace.idea_id)
    }
  }, [messages, workspace?.idea_id, fetchWorkspace])

  useEffect(() => {
    if (!workspace?.idea_id || !connected) return
    const interval = window.setInterval(() => {
      void fetchWorkspace(workspace.idea_id)
    }, activeNodes.length > 0 ? 3000 : 8000)
    return () => window.clearInterval(interval)
  }, [workspace?.idea_id, activeNodes.length, connected, fetchWorkspace])

  return (
    <ScrollArea className="flex-1">
      <div className="flex flex-col gap-3 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Live Activity</p>
          <span
            className={cn('size-1.5 rounded-full', connected ? 'bg-status-validated' : 'bg-muted-foreground')}
            aria-label={connected ? 'Connected' : 'Disconnected'}
          />
        </div>

        {activeNodes.length > 0 && (
          <div className="flex flex-col gap-2">
            {activeNodes.map((node) => (
              <div key={node.node_id} className="rounded-md border border-primary/30 bg-primary/5 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-foreground">{node.title}</p>
                  <Badge variant="warning">Running</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Agent: {node.active_agents.map(resolveAgentDisplayName).join(', ')}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-foreground/90">{getLatestActivity(node)}</p>
              </div>
            ))}
          </div>
        )}

        {messages.length === 0 && activeNodes.length === 0 && (
          <p className="text-sm text-muted-foreground">No agent activity yet. Ask the orchestrator to start research.</p>
        )}

        {messages.slice(-20).map((msg, index) => (
          <div
            key={`${msg.text}-${index}`}
            className={cn(
              'rounded-md border border-border bg-background/60 px-3 py-2 text-xs leading-relaxed',
              msg.type === 'critique' && 'border-status-needs-work/40',
              msg.type === 'error' && 'border-destructive/40',
              msg.type === 'done' && 'border-status-validated/40',
            )}
          >
            <p
              className={cn(
                msg.type === 'critique' && 'text-status-needs-work',
                msg.type === 'error' && 'text-destructive',
                msg.type === 'done' && 'text-status-validated',
              )}
            >
              {msg.text}
            </p>
            {typeof msg.score === 'number' && (
              <p className="mt-1 text-[10px] text-muted-foreground">Score: {msg.score}/100</p>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}

function KnowledgeGraphList() {
  const workspace = useWorkspaceStore((s) => s.workspace)
  const setSelectedNodeId = useWorkspaceStore((s) => s.setSelectedNodeId)

  if (!workspace) {
    return <p className="p-4 text-sm text-muted-foreground">No workspace loaded.</p>
  }

  return (
    <ScrollArea className="flex-1">
      <div className="flex flex-col gap-2 p-4">
        {workspace.nodes.map((node) => (
          <button
            key={node.node_id}
            type="button"
            onClick={() => setSelectedNodeId(node.node_id)}
            className="rounded-md border border-border bg-background/60 p-3 text-left transition-colors hover:border-primary/40 hover:bg-primary/5"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-foreground">{node.title}</p>
              <Badge variant={statusBadgeVariant[node.status]}>{statusLabels[node.status]}</Badge>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
              <span>{node.confidence}% confidence</span>
              <span>{node.source_pills.length} sources</span>
              {node.active_agents.length > 0 && <span>{node.active_agents.length} active agent(s)</span>}
            </div>
            <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-foreground/80">{getLatestActivity(node)}</p>
          </button>
        ))}
      </div>
    </ScrollArea>
  )
}

function OrchestratorChat() {
  const [input, setInput] = useState('')
  const { messages, voiceState, toggleListening, sendMessage } = useVoiceOrchestrator()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!input.trim() || micDisabled) return
    const text = input.trim()
    setInput('')
    await sendMessage(text, { speak: false })
  }

  const micDisabled = voiceState === 'thinking' || voiceState === 'transcribing' || voiceState === 'speaking'

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 p-4">
          {messages.map((msg, index) => (
            <div key={`${msg.text}-${index}`} className={cn('flex flex-col gap-1', msg.role === 'user' && 'items-end')}>
              <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                {msg.role === 'user' ? 'You' : (msg.agentName ?? 'Orchestrator')}
              </span>
              <div
                className={cn(
                  'max-w-[90%] rounded-lg px-3 py-2 text-sm leading-relaxed',
                  msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground/90',
                )}
              >
                {msg.text}
              </div>
              {msg.actionsTaken?.length ? (
                <div className={cn('flex flex-wrap gap-1', msg.role === 'user' && 'justify-end')}>
                  {msg.actionsTaken.map((action) => (
                    <Badge key={action.summary} variant="outline" className="text-[10px]">
                      {action.summary}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <form onSubmit={(e) => void handleSend(e)} className="border-t border-border p-3">
        <div className="relative">
          <Textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask the orchestrator anything…"
            rows={2}
            className="min-h-[60px] resize-none pr-20"
            disabled={micDisabled}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                void handleSend(event)
              }
            }}
          />
          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            <Button
              type="button"
              size="icon"
              variant={voiceState === 'listening' ? 'default' : 'ghost'}
              className="size-8"
              aria-label={voiceState === 'listening' ? 'Stop listening' : 'Start voice input'}
              disabled={micDisabled}
              onClick={() => void toggleListening()}
            >
              {voiceState === 'listening' ? <MicOff className="size-4" /> : <Mic className="size-4" />}
            </Button>
            <Button
              type="submit"
              size="icon"
              variant="ghost"
              className="size-8 text-muted-foreground hover:text-primary"
              aria-label="Send message"
              disabled={!input.trim() || micDisabled}
            >
              <ArrowUp className="size-4" />
            </Button>
          </div>
        </div>
        <p className="mt-2 text-[10px] text-muted-foreground">
          {voiceState === 'listening'
            ? 'Listening… tap mic again to send'
            : voiceState === 'thinking'
              ? 'Orchestrator is thinking…'
              : voiceState === 'speaking'
                ? 'Speaking response…'
                : 'Tap mic for voice, or type a command'}
        </p>
      </form>
    </div>
  )
}

export function OrchestratorPanel() {
  return (
    <aside className="shell-panel flex h-full w-[360px] shrink-0 flex-col border-l border-border bg-card">
      <div className="border-b border-border p-4">
        <h2 className="text-base font-semibold text-foreground">Orchestrator</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Talk or type to manage your startup — research nodes, get updates, and dispatch sub-agents.
        </p>
      </div>

      <Tabs defaultValue="chat" className="flex min-h-0 flex-1 flex-col">
        <TabsList className="w-full justify-start px-4">
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="graph">Knowledge Graph</TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <OrchestratorChat />
        </TabsContent>
        <TabsContent value="activity" className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <ActivityCards />
        </TabsContent>
        <TabsContent value="graph" className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <KnowledgeGraphList />
        </TabsContent>
      </Tabs>
    </aside>
  )
}
