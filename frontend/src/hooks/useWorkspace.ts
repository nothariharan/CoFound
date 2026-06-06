import { useCallback, useState } from 'react'
import type { Workspace } from '@/types'
import { USE_MOCK } from '@/config/env'
import { mockCreateWorkspace, mockFetchWorkspace } from '@/mock/demoEngine'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { MOCK_AWAY_NOTIFICATION } from '@/mock/workspace'

export function useWorkspace() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { setWorkspace, setPhase, setAwayNotification } = useWorkspaceStore()

  const createWorkspace = useCallback(
    async (idea: string) => {
      setLoading(true)
      setError(null)
      try {
        if (USE_MOCK) {
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
        await fetch('/api/agents/spawn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ workspace_id: data.idea_id, trigger: 'session_start' }),
        })
        return data
      } catch (e) {
        const message = e instanceof Error ? e.message : 'Unknown error'
        setError(message)
        throw e
      } finally {
        setLoading(false)
      }
    },
    [setWorkspace, setPhase, setAwayNotification],
  )

  const fetchWorkspace = useCallback(
    async (ideaId: string) => {
      setLoading(true)
      setError(null)
      try {
        if (USE_MOCK) {
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
        return data
      } catch (e) {
        const message = e instanceof Error ? e.message : 'Unknown error'
        setError(message)
        throw e
      } finally {
        setLoading(false)
      }
    },
    [setWorkspace, setPhase],
  )

  return { createWorkspace, fetchWorkspace, loading, error }
}
