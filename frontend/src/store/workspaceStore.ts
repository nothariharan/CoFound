import { create } from 'zustand'
import type {
  AgentInfo,
  AppPhase,
  GraphNode,
  IntegrationInfo,
  ProjectInfo,
  TodayPriority,
  Workspace,
} from '@/types'
import { MOCK_PROJECTS } from '@/mock/workspace'

interface WorkspaceState {
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
  getSelectedNode: () => GraphNode | null
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  phase: 'intake',
  workspace: null,
  selectedNodeId: null,
  todayPriority: {
    action: 'Refine your core idea with more detail',
    reason: 'Core Idea confidence is below validation threshold',
    estimatedTime: '15 min',
  },
  notifications: [],
  healthScore: 0,
  awayNotification: '',
  agents: [
    { id: 'orchestrator', name: 'Orchestrator', status: 'active' },
    { id: 'researcher_1', name: 'Researcher 1', status: 'active', node_id: 'node-audience' },
    { id: 'researcher_2', name: 'Researcher 2', status: 'active', node_id: 'node-market' },
  ],
  integrations: [
    { id: 'github', label: 'GitHub', connected: false },
    { id: 'posthog', label: 'PostHog', connected: false },
    { id: 'gmail', label: 'Gmail', connected: false },
    { id: 'slack', label: 'Slack', connected: false },
    { id: 'gummysearch', label: 'GummySearch', connected: true },
    { id: 'reddit', label: 'Reddit', connected: true },
  ],
  projects: MOCK_PROJECTS,
  pivotBlurredNodes: [],
  demoStage: 0,
  journalOpen: false,
  exportOpen: false,
  setPhase: (phase) => set({ phase }),
  setWorkspace: (workspace) =>
    set({ workspace, selectedNodeId: workspace.nodes.find((n) => n.type === 'market_intelligence')?.node_id ?? workspace.nodes[0]?.node_id ?? null }),
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
  getSelectedNode: () => {
    const { workspace, selectedNodeId } = get()
    if (!workspace || !selectedNodeId) return null
    return workspace.nodes.find((n) => n.node_id === selectedNodeId) ?? null
  },
}))
