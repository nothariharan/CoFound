import { useCallback, useState } from 'react'
import type { Workspace } from '../types'
import { useWorkspaceStore } from '../store/workspaceStore'

export function useWorkspace() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { setWorkspace, setPhase } = useWorkspaceStore()

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
