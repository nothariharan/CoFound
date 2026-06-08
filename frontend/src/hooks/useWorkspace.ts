import { useCallback, useState } from 'react'
import type { TodayPriority, Workspace } from '@/types'
import { mockCreateWorkspace, mockFetchWorkspace } from '@/mock/demoEngine'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { MOCK_AWAY_NOTIFICATION } from '@/mock/workspace'

async function fetchPriority(workspaceId: string): Promise<TodayPriority | null> {
  const res = await fetch(`/api/priority?workspace_id=${encodeURIComponent(workspaceId)}`)
  if (!res.ok) return null
  const data = await res.json()
  return {
    action: data.action,
    reason: data.reason,
    estimatedTime: data.estimated_time ?? data.estimatedTime,
    impact: data.impact,
  }
}

export function useWorkspace() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace)
  const setPhase = useWorkspaceStore((s) => s.setPhase)
  const setAwayNotification = useWorkspaceStore((s) => s.setAwayNotification)
  const setTodayPriority = useWorkspaceStore((s) => s.setTodayPriority)

  const createWorkspace = useCallback(
    async (idea: string) => {
      setLoading(true)
      setError(null)
      try {
        if (useWorkspaceStore.getState().mode === 'demo') {
          const data = await mockCreateWorkspace(idea)
          setAwayNotification(MOCK_AWAY_NOTIFICATION)
          return data
        }
        const res = await fetch('/api/workspace', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ idea }),
        })
        if (!res.ok) throw new Error('Failed to create workspace')
        const data: Workspace = await res.json()
        setWorkspace(data)
        setPhase('dashboard')

        const spawnRes = await fetch('/api/agents/spawn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ workspace_id: data.idea_id, trigger: 'session_start' }),
        })
        if (!spawnRes.ok) {
          const detail = await spawnRes.text()
          throw new Error(detail || 'Failed to spawn agents')
        }

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
    [setWorkspace, setPhase, setAwayNotification, setTodayPriority],
  )

  const fetchWorkspace = useCallback(
    async (ideaId: string) => {
      setLoading(true)
      setError(null)
      try {
        if (useWorkspaceStore.getState().mode === 'demo') {
          const data = await mockFetchWorkspace(ideaId)
          setWorkspace(data)
          setPhase('dashboard')
          return data
        }
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
