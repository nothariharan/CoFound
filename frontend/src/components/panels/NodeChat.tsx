import { useState } from 'react'
import { ArrowUp } from 'lucide-react'
import type { GraphNode } from '@/types'
import { MOCK_CHAT_MESSAGES } from '@/mock/workspace'
import { triggerPivotDemo } from '@/mock/demoEngine'
import { USE_MOCK } from '@/config/env'
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
  const [messages, setMessages] = useState(MOCK_CHAT_MESSAGES)
  const { workspace, setPivotBlurredNodes } = useWorkspaceStore()

  const mapNodeTypesToIds = (nodesAffected: string[]) => {
    if (!workspace) return []
    return workspace.nodes
      .filter((n) => nodesAffected.includes(n.type) || nodesAffected.includes(n.node_id))
      .map((n) => n.node_id)
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMsg = input.trim()
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }])
    setInput('')

    if (userMsg.toLowerCase().includes('pivot')) {
      if (USE_MOCK) {
        triggerPivotDemo()
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              role: 'agent',
              agentName: 'Diff Classifier',
              text: 'Pivot detected. Re-researching Audience and Competitors while keeping Core Idea intact.',
            },
          ])
        }, 500)
      } else if (workspace?.idea_id) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'agent',
            agentName: 'Diff Classifier',
            text: 'Analyzing pivot and identifying affected nodes...',
          },
        ])
        try {
          const res = await fetch('/api/agents/pivot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace_id: workspace.idea_id, message: userMsg }),
          })
          if (!res.ok) throw new Error('Pivot request failed')
          const data = await res.json()
          const blurredNodeIds = mapNodeTypesToIds(data.nodes_affected ?? [])
          setPivotBlurredNodes(blurredNodeIds)
          setTimeout(() => setPivotBlurredNodes([]), 3000)
          setMessages((prev) => [
            ...prev,
            {
              role: 'agent',
              agentName: 'Diff Classifier',
              text: `Pivot detected. Re-researching ${blurredNodeIds.length || data.nodes_affected?.length || 0} node(s).`,
            },
          ])
        } catch {
          setMessages((prev) => [
            ...prev,
            {
              role: 'agent',
              agentName: 'Diff Classifier',
              text: 'Pivot request failed. Please try again.',
            },
          ])
        }
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'agent',
            agentName: 'Diff Classifier',
            text: 'Pivot is unavailable until the workspace is loaded.',
          },
        ])
      }
      return
    }

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          agentName: 'Researcher 2',
          text: `Based on current ${node.title} data, I can help refine this further. What specific aspect would you like to explore?`,
        },
      ])
    }, 600)
  }

  return (
    <div className="flex h-full flex-col">
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 p-4">
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
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend(e)
              }
            }}
          />
          <Button
            type="submit"
            size="icon"
            variant="ghost"
            className="absolute bottom-2 right-2 size-8 text-muted-foreground hover:text-primary"
            aria-label="Send message"
            disabled={!input.trim()}
          >
            <ArrowUp className="size-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}
