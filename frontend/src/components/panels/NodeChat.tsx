import { useEffect, useState } from 'react'
import { ArrowUp } from 'lucide-react'
import type { ChatMessage, GraphNode } from '@/types'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

interface NodeChatProps {
  node: GraphNode
}

export function NodeChat({ node }: NodeChatProps) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sending, setSending] = useState(false)
  const { sendDialogue, sendPivot, sendOrchestratorChat } = useAgentActions()
  const { workspace, pivotBlurredNodes, setPivotBlurredNodes, setHasChatted } = useWorkspaceStore()
  const isCoreIdea = node.type === 'core_idea'
  const thinkingLabel = isCoreIdea ? 'CoFound' : 'Dialogue Agent'

  useEffect(() => {
    if (!workspace || pivotBlurredNodes.length === 0) return
    const stillActive = workspace.nodes.some(
      (graphNode) => pivotBlurredNodes.includes(graphNode.node_id) && graphNode.active_agents.length > 0,
    )
    if (!stillActive) setPivotBlurredNodes([])
  }, [workspace, pivotBlurredNodes, setPivotBlurredNodes])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return

    const userMsg = input.trim()
    const nextHistory: ChatMessage[] = [...messages, { role: 'user', text: userMsg }]
    setMessages(nextHistory)
    setInput('')
    setSending(true)
    setHasChatted(true)

    try {
      if (!workspace?.idea_id) return

      if (userMsg.toLowerCase().includes('pivot')) {
        const pivot = await sendPivot(workspace.idea_id, userMsg)
        setPivotBlurredNodes(
          workspace.nodes.filter((n) => pivot.nodes_affected.includes(n.type)).map((n) => n.node_id),
        )
        setMessages((prev) => [
          ...prev,
          {
            role: 'agent',
            agentName: 'Diff Classifier',
            text: `Pivot detected. ${pivot.nodes_affected.join(', ').replace(/_/g, ' ')} now need your approval before re-research. Preserved ${pivot.nodes_unchanged.slice(0, 3).join(', ').replace(/_/g, ' ')}.`,
          },
        ])
        return
      }

      if (isCoreIdea) {
        const result = await sendOrchestratorChat(workspace.idea_id, userMsg, nextHistory)
        setMessages((prev) => [
          ...prev,
          { role: 'agent', agentName: 'CoFound', text: result.reply },
        ])
        return
      }

      const dialogue = await sendDialogue(workspace.idea_id, userMsg)
      setMessages((prev) => [
        ...prev,
        { role: 'agent', agentName: 'Dialogue Agent', text: dialogue.brief },
        { role: 'agent', agentName: 'Dialogue Agent', text: dialogue.question },
      ])
    } catch (e: unknown) {
      const status = e instanceof ApiError ? e.status : (e as { status?: number })?.status
      const message = e instanceof Error ? e.message : ''
      const text =
        status === 503 || status === 502 || status === 504
          ? 'The agent is warming up or temporarily busy. Please try again in a moment.'
          : message || 'The agent could not respond. Please try again.'
      setMessages((prev) => [...prev, { role: 'agent', agentName: 'System', text }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex h-full flex-col" data-onboarding="node-chat">
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 p-4">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">
              {isCoreIdea
                ? 'Ask about your idea, request research, or type "pivot" to re-scope the graph.'
                : `Ask about ${node.title.toLowerCase()} or type "pivot" to re-research.`}
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={cn('flex flex-col gap-1', msg.role === 'user' && 'items-end')}>
              <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                {msg.role === 'user' ? 'You' : (msg.agentName ?? 'Agent')}
              </span>
              <div
                className={cn(
                  'max-w-[90%] rounded-lg px-3 py-2 text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground/90',
                )}
              >
                {msg.text}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex flex-col gap-1" role="status" aria-live="polite">
              <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                {thinkingLabel}
              </span>
              <div className="flex w-fit items-center gap-1.5 rounded-lg bg-muted px-3 py-2">
                <span className="size-1.5 animate-pulse rounded-full bg-primary" />
                <span className="size-1.5 animate-pulse rounded-full bg-primary [animation-delay:150ms]" />
                <span className="size-1.5 animate-pulse rounded-full bg-primary [animation-delay:300ms]" />
                <span className="ml-1 text-xs text-muted-foreground">Thinking…</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <form onSubmit={(e) => void handleSend(e)} className="border-t border-border p-3">
        <div className="relative">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isCoreIdea
                ? 'Ask CoFound about your idea…'
                : `Ask about ${node.title.toLowerCase()}...`
            }
            rows={2}
            className="min-h-[60px] resize-none pr-10"
            disabled={sending}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void handleSend(e)
              }
            }}
          />
          <Button
            type="submit"
            size="icon"
            variant="ghost"
            className="absolute bottom-2 right-2 size-8 text-muted-foreground hover:text-primary"
            aria-label="Send message"
            disabled={!input.trim() || sending}
          >
            {sending ? (
              <span className="size-4 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary" />
            ) : (
              <ArrowUp className="size-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
