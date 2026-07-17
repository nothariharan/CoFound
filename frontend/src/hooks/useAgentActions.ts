import { useCallback, useState } from 'react'
import { apiFetch, apiUrl } from '@/lib/api'
import type { ChatMessage, JournalEntry, OrchestratorChatResult, TodayPriority } from '@/types'
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
}

export interface ConnectResult {
  connected: boolean
  build_node_unlocked?: boolean
  observe_node_unlocked?: boolean
}

export interface ResearchNodeResult {
  session_id: string
  tasks_queued: number
  agents_active: number
}

export function useAgentActions() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendOrchestratorChat = useCallback(
    async (
      workspaceId: string,
      message: string,
      history?: ChatMessage[],
    ): Promise<OrchestratorChatResult> => {
      const res = await apiFetch('/api/orchestrator/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceId,
          message,
          history: (history ?? []).map((item) => ({ role: item.role, text: item.text })),
        }),
      })
      return res.json()
    },
    [],
  )

  const sendDialogue = useCallback(
    async (workspaceId: string, message?: string): Promise<DialogueResult> => {
      const res = await apiFetch('/api/agents/dialogue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, message }),
      })
      return res.json()
    },
    [],
  )

  const sendPivot = useCallback(
    async (workspaceId: string, message: string): Promise<PivotResult> => {
      const res = await apiFetch('/api/agents/pivot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, message }),
      })
      return res.json()
    },
    [],
  )

  const fetchJournal = useCallback(
    async (workspaceId: string): Promise<JournalEntry[]> => {
      const res = await fetch(apiUrl(`/api/workspace/${workspaceId}/journal`))
      if (!res.ok) throw new Error('Failed to fetch journal')
      const data = await res.json()
      return (data.entries ?? []) as JournalEntry[]
    },
    [],
  )

  const requestExport = useCallback(
    async (workspaceId: string): Promise<ExportResult> => {
      const res = await fetch(apiUrl('/api/export'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId }),
      })
      if (!res.ok) throw new Error('Failed to generate export')
      return res.json()
    },
    [],
  )

  const fetchPriority = useCallback(
    async (workspaceId: string): Promise<TodayPriority> => {
      const res = await fetch(apiUrl(`/api/priority?workspace_id=${encodeURIComponent(workspaceId)}`))
      if (!res.ok) throw new Error('Failed to fetch priority')
      const data = await res.json()
      return {
        action: data.action,
        reason: data.reason,
        estimatedTime: data.estimated_time ?? data.estimatedTime,
        impact: data.impact,
        nodeType: data.node_type ?? data.nodeType,
        nodeId: data.node_id ?? data.nodeId,
      }
    },
    [],
  )

  const handoffToOrchestrator = useCallback(
    async (workspaceId: string): Promise<ResearchNodeResult> => {
      const res = await fetch(apiUrl('/api/agents/handoff-priority'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId }),
      })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || 'Failed to hand off priority to orchestrator')
      }
      return res.json()
    },
    [],
  )

  const fetchIntegrations = useCallback(
    async (workspaceId: string): Promise<IntegrationStatus> => {
      const res = await fetch(apiUrl(`/api/integrations?workspace_id=${encodeURIComponent(workspaceId)}`))
      if (!res.ok) throw new Error('Failed to fetch integrations')
      return res.json()
    },
    [],
  )

  const researchNode = useCallback(
    async (workspaceId: string, nodeType: string, userContext?: string): Promise<ResearchNodeResult> => {
      const res = await fetch(apiUrl('/api/agents/research-node'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceId,
          node_type: nodeType,
          user_context: userContext || null,
        }),
      })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || 'Failed to start node research')
      }
      return res.json()
    },
    [],
  )

  const spawnCustomTask = useCallback(
    async (
      workspaceId: string,
      title: string,
      description: string,
      nodeType?: string,
    ): Promise<ResearchNodeResult> => {
      const res = await fetch(apiUrl('/api/agents/custom-task'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceId,
          title,
          description,
          node_type: nodeType || null,
        }),
      })
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || 'Failed to spawn custom task')
      }
      return res.json()
    },
    [],
  )

  const connectGithub = useCallback(
    async (workspaceId: string, repo: string, accessToken?: string): Promise<ConnectResult> => {
      const res = await fetch(apiUrl('/api/integrations/github'), {
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
    [],
  )

  const connectPosthog = useCallback(
    async (workspaceId: string, projectId: string, apiKey: string): Promise<ConnectResult> => {
      const res = await fetch(apiUrl('/api/integrations/posthog'), {
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
    [],
  )

  return {
    sendOrchestratorChat,
    sendDialogue,
    sendPivot,
    fetchJournal,
    requestExport,
    fetchPriority,
    handoffToOrchestrator,
    fetchIntegrations,
    researchNode,
    spawnCustomTask,
    connectGithub,
    connectPosthog,
    loading,
    error,
    setLoading,
    setError,
  }
}
