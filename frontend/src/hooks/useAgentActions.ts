import { useCallback, useState } from 'react'
import type { JournalEntry, TodayPriority } from '@/types'
import { MOCK_EXPORT_FILES, MOCK_JOURNAL } from '@/mock/workspace'
import { useWorkspaceStore } from '@/store/workspaceStore'

export interface DialogueResult {
  brief: string
  question: string
}

export interface PivotResult {
  nodes_affected: string[]
  nodes_unchanged: string[]
  requery_needed: boolean
  spawn_researcher: boolean
}

export interface ExportResult {
  export_url: string
  files: string[]
}

export interface IntegrationStatus {
  github: boolean
  posthog: boolean
  reddit: boolean
  gummysearch: boolean
}

export interface ConnectResult {
  connected: boolean
  build_node_unlocked?: boolean
  observe_node_unlocked?: boolean
}

export function useAgentActions() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isDemoMode = useCallback(() => useWorkspaceStore.getState().mode === 'demo', [])

  const sendDialogue = useCallback(
    async (workspaceId: string, message?: string): Promise<DialogueResult> => {
      if (isDemoMode()) {
        return {
          brief: 'Graph synthesized from demo workspace.',
          question:
            'What is the single customer segment with the highest urgency and easiest first distribution channel?',
        }
      }
      const res = await fetch('/api/agents/dialogue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, message }),
      })
      if (!res.ok) throw new Error('Failed to get dialogue response')
      return res.json()
    },
    [isDemoMode],
  )

  const sendPivot = useCallback(
    async (workspaceId: string, message: string): Promise<PivotResult> => {
      if (isDemoMode()) {
        return {
          nodes_affected: ['audience', 'competitors'],
          nodes_unchanged: ['core_idea', 'market_intelligence'],
          requery_needed: true,
          spawn_researcher: true,
        }
      }
      const res = await fetch('/api/agents/pivot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, message }),
      })
      if (!res.ok) throw new Error('Failed to process pivot')
      return res.json()
    },
    [isDemoMode],
  )

  const fetchJournal = useCallback(
    async (workspaceId: string): Promise<JournalEntry[]> => {
      if (isDemoMode()) return MOCK_JOURNAL
      const res = await fetch(`/api/workspace/${workspaceId}/journal`)
      if (!res.ok) throw new Error('Failed to fetch journal')
      const data = await res.json()
      return (data.entries ?? []) as JournalEntry[]
    },
    [isDemoMode],
  )

  const requestExport = useCallback(
    async (workspaceId: string): Promise<ExportResult> => {
      if (isDemoMode()) {
        return { export_url: '', files: MOCK_EXPORT_FILES }
      }
      const res = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId }),
      })
      if (!res.ok) throw new Error('Failed to generate export')
      return res.json()
    },
    [isDemoMode],
  )

  const fetchPriority = useCallback(
    async (workspaceId: string): Promise<TodayPriority> => {
      if (isDemoMode()) {
        return {
          action: 'Talk to 3 restaurant owners',
          reason: 'Audience confidence is 72% — highest ROI action today',
          estimatedTime: '2 hrs',
          impact: 'High impact',
        }
      }
      const res = await fetch(`/api/priority?workspace_id=${encodeURIComponent(workspaceId)}`)
      if (!res.ok) throw new Error('Failed to fetch priority')
      const data = await res.json()
      return {
        action: data.action,
        reason: data.reason,
        estimatedTime: data.estimated_time ?? data.estimatedTime,
        impact: data.impact,
      }
    },
    [isDemoMode],
  )

  const fetchIntegrations = useCallback(
    async (workspaceId: string): Promise<IntegrationStatus> => {
      if (isDemoMode()) {
        return { github: false, posthog: false, reddit: true, gummysearch: true }
      }
      const res = await fetch(`/api/integrations?workspace_id=${encodeURIComponent(workspaceId)}`)
      if (!res.ok) throw new Error('Failed to fetch integrations')
      return res.json()
    },
    [isDemoMode],
  )

  const connectGithub = useCallback(
    async (workspaceId: string, repo: string, accessToken?: string): Promise<ConnectResult> => {
      if (isDemoMode()) {
        return { connected: true, build_node_unlocked: true }
      }
      const res = await fetch('/api/integrations/github', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceId,
          repo,
          access_token: accessToken || null,
        }),
      })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || 'Failed to connect GitHub')
      }
      return res.json()
    },
    [isDemoMode],
  )

  const connectPosthog = useCallback(
    async (workspaceId: string, projectId: string, apiKey: string): Promise<ConnectResult> => {
      if (isDemoMode()) {
        return { connected: true, observe_node_unlocked: true }
      }
      const res = await fetch('/api/integrations/posthog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceId,
          project_id: projectId,
          api_key: apiKey,
        }),
      })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || 'Failed to connect PostHog')
      }
      return res.json()
    },
    [isDemoMode],
  )

  return {
    sendDialogue,
    sendPivot,
    fetchJournal,
    requestExport,
    fetchPriority,
    fetchIntegrations,
    connectGithub,
    connectPosthog,
    loading,
    error,
    setLoading,
    setError,
  }
}
