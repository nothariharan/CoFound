import { useState } from 'react'
import { Send } from 'lucide-react'
import type { GraphNode } from '../../types'

interface NodeChatProps {
  node: GraphNode
}

export function NodeChat({ node }: NodeChatProps) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{ role: 'user' | 'agent'; text: string }[]>([])

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    setMessages((prev) => [
      ...prev,
      { role: 'user', text: input },
      {
        role: 'agent',
        text: `Research for ${node.title} will be available once agents are connected.`,
      },
    ])
    setInput('')
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-[#e5e5e5] px-4 py-3">
        <h3 className="text-sm font-semibold text-[#171717]">Node Chat</h3>
        <p className="text-xs text-[#737373]">Scoped to {node.title}</p>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-xs text-[#737373]">
            Ask a targeted question about this node.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-sm ${msg.role === 'user' ? 'text-[#171717]' : 'text-[#737373]'}`}
          >
            <span className="text-[10px] font-medium uppercase tracking-wide">
              {msg.role === 'user' ? 'You' : 'Agent'}
            </span>
            <p className="mt-0.5">{msg.text}</p>
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} className="border-t border-[#e5e5e5] p-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this node..."
            className="flex-1 rounded border border-[#e5e5e5] px-3 py-2 text-sm focus:border-[#2563eb] focus:outline-none"
          />
          <button
            type="submit"
            className="rounded border border-[#e5e5e5] p-2 text-[#737373] hover:border-[#d4d4d4]"
          >
            <Send size={16} strokeWidth={1.5} />
          </button>
        </div>
      </form>
    </div>
  )
}
