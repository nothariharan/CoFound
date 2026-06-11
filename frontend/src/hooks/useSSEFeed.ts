import { useEffect, useRef, useState } from 'react'
import type { FeedMessage, Workspace } from '@/types'
import { useWorkspaceStore } from '@/store/workspaceStore'

type SSEPayload =
  | FeedMessage
  | {
      type: 'workspace'
      workspace: Workspace
      text?: string
    }

export function useSSEFeed(workspaceId?: string) {
  const [messages, setMessages] = useState<FeedMessage[]>([])
  const [connected, setConnected] = useState(false)
  const sourceRef = useRef<EventSource | null>(null)
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace)

  useEffect(() => {
    setMessages([])
    setConnected(false)

    const url = workspaceId ? `/api/feed?workspace_id=${workspaceId}` : '/api/feed'
    const source = new EventSource(url)
    sourceRef.current = source

    source.onopen = () => setConnected(true)
    source.onerror = () => setConnected(false)

    source.onmessage = (event) => {
      try {
        const data: SSEPayload = JSON.parse(event.data)
        if (data.type === 'workspace') {
          setWorkspace(data.workspace)
          return
        }
        if (data.type === 'ping' || !data.text) return
        setMessages((prev) => [...prev, data])
      } catch {
        // ignore malformed events
      }
    }

    return () => {
      source.close()
      sourceRef.current = null
    }
  }, [workspaceId, setWorkspace])

  return { messages, connected }
}
