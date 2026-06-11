import { useEffect, useState } from 'react'
import { ArrowUp } from 'lucide-react'
import type { ChatMessage, GraphNode } from '@/types'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspaceStore } from '@/store/workspaceStore'
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
  const { sendDialogue, sendPivot } = useAgentActions()
  const { workspace, pivotBlurredNodes, setPivotBlurredNodes, setHasChatted } = useWorkspaceStore()

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
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }])
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

      const dialogue = await sendDialogue(workspace.idea_id, userMsg)
      setMessages((prev) => [
        ...prev,
        { role: 'agent', agentName: 'Dialogue Agent', text: dialogue.brief },
        { role: 'agent', agentName: 'Dialogue Agent', text: dialogue.question },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'agent', agentName: 'System', text: 'Failed to reach the agent. Check that the backend is running.' },
      ])
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
              Ask about {node.title.toLowerCase()} or type &quot;pivot&quot; to re-research.
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
        </div>
      </ScrollArea>

      <form onSubmit={handleSend} className="border-t border-border p-3">
        <div className="relative">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask about ${node.title.toLowerCase()}...`}
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
            <ArrowUp className="size-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}
