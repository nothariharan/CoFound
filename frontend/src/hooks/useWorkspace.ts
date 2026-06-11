import { useCallback, useState } from 'react'
import type { TodayPriority, Workspace } from '@/types'
import { useWorkspaceStore } from '@/store/workspaceStore'

async function fetchPriority(workspaceId: string): Promise<TodayPriority | null> {
  const res = await fetch(`/api/priority?workspace_id=${encodeURIComponent(workspaceId)}`)
  if (!res.ok) return null
  const data = await res.json()
  return {
    action: data.action,
    reason: data.reason,
    estimatedTime: data.estimated_time ?? data.estimatedTime,
    impact: data.impact,
    nodeType: data.node_type ?? data.nodeType,
    nodeId: data.node_id ?? data.nodeId,
  }
}

export function useWorkspace() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace)
  const setPhase = useWorkspaceStore((s) => s.setPhase)
  const setTodayPriority = useWorkspaceStore((s) => s.setTodayPriority)

  const createWorkspace = useCallback(
    async (idea: string) => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('/api/workspace', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ idea }),
        })
        if (!res.ok) throw new Error('Failed to create workspace')
        const data: Workspace = await res.json()
        setWorkspace(data)
        setPhase('dashboard')

        const priority = await fetchPriority(data.idea_id)
        if (priority) setTodayPriority(priority)

        return data
      } catch (e) {
        const message = e instanceof Error ? e.message : 'Unknown error'
        setError(message)
        throw e
      } finally {
        setLoading(false)
      }
    },
    [setWorkspace, setPhase, setTodayPriority],
  )

  const fetchWorkspace = useCallback(
    async (ideaId: string) => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/workspace/${ideaId}`)
        if (!res.ok) throw new Error('Workspace not found')
        const data: Workspace = await res.json()
        setWorkspace(data)
        setPhase('dashboard')

        const priority = await fetchPriority(ideaId)
        if (priority) setTodayPriority(priority)

        return data
      } catch (e) {
        const message = e instanceof Error ? e.message : 'Unknown error'
        setError(message)
        throw e
      } finally {
        setLoading(false)
      }
    },
    [setWorkspace, setPhase, setTodayPriority],
  )

  return { createWorkspace, fetchWorkspace, loading, error }
}
