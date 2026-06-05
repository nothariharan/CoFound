import { useEffect, useRef, useState } from 'react'
import type { FeedMessage } from '@/types'
import { USE_MOCK } from '@/config/env'
import { subscribeFeed } from '@/mock/demoEngine'

export function useSSEFeed(workspaceId?: string) {
  const [messages, setMessages] = useState<FeedMessage[]>([])
  const [connected, setConnected] = useState(false)
  const sourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (USE_MOCK) {
      setConnected(true)
      const unsub = subscribeFeed((msg) => {
        if (msg.type === 'ping' || !msg.text) return
        setMessages((prev) => [...prev, msg])
      })
      return () => {
        unsub()
        setConnected(false)
      }
    }

    const url = workspaceId ? `/api/feed?workspace_id=${workspaceId}` : '/api/feed'
    const source = new EventSource(url)
    sourceRef.current = source

    source.onopen = () => setConnected(true)
    source.onerror = () => setConnected(false)

    source.onmessage = (event) => {
      try {
        const data: FeedMessage = JSON.parse(event.data)
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
  }, [workspaceId])

  return { messages, connected }
}
