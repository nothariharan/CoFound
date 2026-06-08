import { create } from 'zustand'
import type {
  AgentInfo,
  AppMode,
  AppPhase,
  GraphNode,
  IntegrationInfo,
  ProjectInfo,
  TodayPriority,
  Workspace,
} from '@/types'
import { USE_MOCK } from '@/config/env'
import { INTEGRATION_CATALOG } from '@/config/integrations'
import { MOCK_PROJECTS } from '@/mock/workspace'

const DEFAULT_MODE: AppMode = USE_MOCK ? 'demo' : 'live'

function deriveAgents(workspace: Workspace | null): AgentInfo[] {
  if (!workspace) return [{ id: 'orchestrator', name: 'Orchestrator', status: 'active' }]
  const fromNodes = workspace.nodes.flatMap((n) =>
    n.active_agents.map((id) => ({
      id,
      name: id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      status: 'active' as const,
      node_id: n.node_id,
    })),
  )
  if (fromNodes.length) return fromNodes
  return [{ id: 'orchestrator', name: 'Orchestrator', status: 'active' }]
}

const DEFAULT_TODAY_PRIORITY: TodayPriority = {
  action: 'Analyzing your idea...',
  reason: 'Agents are researching your startup graph',
  estimatedTime: '—',
}

interface WorkspaceState {
  mode: AppMode
  phase: AppPhase
  workspace: Workspace | null
  selectedNodeId: string | null
  todayPriority: TodayPriority
  notifications: string[]
  healthScore: number
  awayNotification: string
  agents: AgentInfo[]
  integrations: IntegrationInfo[]
  projects: ProjectInfo[]
  pivotBlurredNodes: string[]
  demoStage: number
  journalOpen: boolean
  exportOpen: boolean
  onboardingOpen: boolean
  integrationDialogId: string | null
  hasChatted: boolean
  hasExported: boolean
  setMode: (mode: AppMode) => void
  setPhase: (phase: AppPhase) => void
  setWorkspace: (workspace: Workspace) => void
  updateNode: (nodeId: string, patch: Partial<GraphNode>) => void
  setSelectedNodeId: (id: string | null) => void
  setTodayPriority: (priority: TodayPriority) => void
  setNotifications: (notifications: string[]) => void
  setHealthScore: (score: number) => void
  setAwayNotification: (msg: string) => void
  setAgents: (agents: AgentInfo[]) => void
  setIntegrations: (integrations: IntegrationInfo[]) => void
  setPivotBlurredNodes: (ids: string[]) => void
  setDemoStage: (stage: number) => void
  setJournalOpen: (open: boolean) => void
  setExportOpen: (open: boolean) => void
  setOnboardingOpen: (open: boolean) => void
  setIntegrationDialogId: (id: string | null) => void
  setHasChatted: (value: boolean) => void
  setHasExported: (value: boolean) => void
  resetToHome: () => void
  getSelectedNode: () => GraphNode | null
  isDemo: () => boolean
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  mode: DEFAULT_MODE,
  phase: 'intake',
  workspace: null,
  selectedNodeId: null,
  todayPriority: DEFAULT_TODAY_PRIORITY,
  notifications: [],
  healthScore: 0,
  awayNotification: '',
  agents: [{ id: 'orchestrator', name: 'Orchestrator', status: 'active' }],
  integrations: INTEGRATION_CATALOG.map((i) => ({ ...i })),
  projects: MOCK_PROJECTS,
  pivotBlurredNodes: [],
  demoStage: 0,
  journalOpen: false,
  exportOpen: false,
  onboardingOpen: false,
  integrationDialogId: null,
  hasChatted: false,
  hasExported: false,
  setMode: (mode) => set({ mode }),
  setPhase: (phase) => set({ phase }),
  setWorkspace: (workspace) =>
    set({
      workspace,
      agents: deriveAgents(workspace),
      selectedNodeId:
        workspace.nodes.find((n) => n.type === 'market_intelligence')?.node_id ??
        workspace.nodes[0]?.node_id ??
        null,
    }),
  updateNode: (nodeId, patch) =>
    set((s) => ({
      workspace: s.workspace
        ? {
            ...s.workspace,
            nodes: s.workspace.nodes.map((n) => (n.node_id === nodeId ? { ...n, ...patch } : n)),
          }
        : null,
    })),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setTodayPriority: (priority) => set({ todayPriority: priority }),
  setNotifications: (notifications) => set({ notifications }),
  setHealthScore: (score) => set({ healthScore: score }),
  setAwayNotification: (msg) => set({ awayNotification: msg }),
  setAgents: (agents) => set({ agents }),
  setIntegrations: (integrations) => set({ integrations }),
  setPivotBlurredNodes: (ids) => set({ pivotBlurredNodes: ids }),
  setDemoStage: (stage) => set({ demoStage: stage }),
  setJournalOpen: (open) => set({ journalOpen: open }),
  setExportOpen: (open) => set({ exportOpen: open }),
  setOnboardingOpen: (open) => set({ onboardingOpen: open }),
  setIntegrationDialogId: (id) => set({ integrationDialogId: id }),
  setHasChatted: (value) => set({ hasChatted: value }),
  setHasExported: (value) => set({ hasExported: value }),
  resetToHome: () =>
    set({
      mode: DEFAULT_MODE,
      phase: 'intake',
      workspace: null,
      selectedNodeId: null,
      todayPriority: DEFAULT_TODAY_PRIORITY,
      notifications: [],
      healthScore: 0,
      awayNotification: '',
      agents: [{ id: 'orchestrator', name: 'Orchestrator', status: 'active' }],
      integrations: INTEGRATION_CATALOG.map((i) => ({ ...i })),
      projects: MOCK_PROJECTS,
      pivotBlurredNodes: [],
      demoStage: 0,
      journalOpen: false,
      exportOpen: false,
      onboardingOpen: false,
      integrationDialogId: null,
      hasChatted: false,
      hasExported: false,
    }),
  getSelectedNode: () => {
    const { workspace, selectedNodeId } = get()
    if (!workspace || !selectedNodeId) return null
    return workspace.nodes.find((n) => n.node_id === selectedNodeId) ?? null
  },
  isDemo: () => get().mode === 'demo',
}))
