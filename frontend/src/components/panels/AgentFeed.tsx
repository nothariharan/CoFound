import { useEffect, useRef } from 'react'
import { useSSEFeed } from '../../hooks/useSSEFeed'
import { useWorkspaceStore } from '../../store/workspaceStore'

export function AgentFeed() {
  const { workspace } = useWorkspaceStore()
  const { messages, connected } = useSSEFeed(workspace?.idea_id)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-[#e5e5e5] px-4 py-3">
        <span className="text-xs font-medium uppercase tracking-wide text-[#737373]">
          Agent Feed
        </span>
        <span
          className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-[#16a34a]' : 'bg-[#a3a3a3]'}`}
        />
      </div>
      <div className="flex-1 overflow-y-auto bg-[#171717] p-4 font-mono text-xs leading-relaxed text-[#e5e5e5]">
        {messages.length === 0 && (
          <p className="text-[#737373]">Waiting for agent activity...</p>
        )}
        {messages.map((msg, i) => (
          <p key={i} className="mb-1">
            {msg.text}
          </p>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
