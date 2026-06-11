import { create } from 'zustand'
import type {
  AgentInfo,
  AppPhase,
  ChatMessage,
  GraphNode,
  IntegrationInfo,
  ProjectInfo,
  TodayPriority,
  VoiceState,
  Workspace,
} from '@/types'
import { INTEGRATION_CATALOG } from '@/config/integrations'
import { resetVoiceSession } from '@/lib/voiceRecorder'
import { getNodeAgentConfig } from '@/config/nodeAgents'
import { NODE_LAYOUT } from '@/utils/canvasLayout'

function deriveAgents(workspace: Workspace | null): AgentInfo[] {
  const orchestrator: AgentInfo = {
    id: 'orchestrator',
    name: 'Orchestrator',
    status: workspace ? 'active' : 'active',
  }
  if (!workspace) return [orchestrator]

  const subAgents: AgentInfo[] = NODE_LAYOUT.flatMap((layout) => {
    const node = workspace.nodes.find((n) => n.node_id === layout.node_id)
    if (!node) return []
    const config = getNodeAgentConfig(node.type)
    let status: AgentInfo['status'] = 'idle'
    if (node.active_agents.length > 0) status = 'active'
    else if (node.status === 'locked') status = 'offline'

    return [
      {
        id: config.id,
        name: config.name,
        status,
        node_id: node.node_id,
        parentId: 'orchestrator',
        nodeType: node.type,
      },
    ]
  })

  return [orchestrator, ...subAgents]
}

const DEFAULT_TODAY_PRIORITY: TodayPriority = {
  action: 'Approve the next research node',
  reason: 'Research will only run after you confirm a specific node.',
  estimatedTime: '—',
}

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
  journalOpen: boolean
  exportOpen: boolean
  settingsOpen: boolean
  onboardingOpen: boolean
  integrationDialogId: string | null
  hasChatted: boolean
  hasExported: boolean
  orchestratorMessages: ChatMessage[]
  voiceState: VoiceState
  orbExpanded: boolean
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
  setJournalOpen: (open: boolean) => void
  setExportOpen: (open: boolean) => void
  setSettingsOpen: (open: boolean) => void
  setOnboardingOpen: (open: boolean) => void
  setIntegrationDialogId: (id: string | null) => void
  setHasChatted: (value: boolean) => void
  setHasExported: (value: boolean) => void
  setOrchestratorMessages: (messages: ChatMessage[]) => void
  appendOrchestratorMessage: (message: ChatMessage) => void
  setVoiceState: (state: VoiceState) => void
  setOrbExpanded: (expanded: boolean) => void
  resetToHome: () => void
  getSelectedNode: () => GraphNode | null
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  phase: 'intake',
  workspace: null,
  selectedNodeId: null,
  todayPriority: DEFAULT_TODAY_PRIORITY,
  notifications: [],
  healthScore: 0,
  awayNotification: '',
  agents: [{ id: 'orchestrator', name: 'Orchestrator', status: 'active' }],
  integrations: INTEGRATION_CATALOG.map((i) => ({ ...i })),
  projects: [],
  pivotBlurredNodes: [],
  journalOpen: false,
  exportOpen: false,
  settingsOpen: false,
  onboardingOpen: false,
  integrationDialogId: null,
  hasChatted: false,
  hasExported: false,
  orchestratorMessages: [],
  voiceState: 'idle',
  orbExpanded: false,
  setPhase: (phase) => set({ phase }),
  setWorkspace: (workspace) =>
    set((state) => {
      const isFirstLoad = state.workspace === null
      const previousSelection = state.selectedNodeId
      const selectionStillValid =
        previousSelection !== null &&
        workspace.nodes.some((node) => node.node_id === previousSelection)

      let selectedNodeId = previousSelection
      if (isFirstLoad) {
        selectedNodeId =
          workspace.nodes.find((node) => node.type === 'market_intelligence')?.node_id ??
          workspace.nodes[0]?.node_id ??
          null
      } else if (previousSelection === null) {
        selectedNodeId = null
      } else if (!selectionStillValid) {
        selectedNodeId = null
      }

      return {
        workspace,
        agents: deriveAgents(workspace),
        selectedNodeId,
      }
    }),
  updateNode: (nodeId, patch) =>
    set((s) => {
      if (!s.workspace) return { workspace: null }
      const nodes = s.workspace.nodes.map((n) => (n.node_id === nodeId ? { ...n, ...patch } : n))
      const workspace = { ...s.workspace, nodes }
      const shouldRefreshAgents =
        patch.active_agents !== undefined || patch.status !== undefined
      return {
        workspace,
        ...(shouldRefreshAgents ? { agents: deriveAgents(workspace) } : {}),
      }
    }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setTodayPriority: (priority) => set({ todayPriority: priority }),
  setNotifications: (notifications) => set({ notifications }),
  setHealthScore: (score) => set({ healthScore: score }),
  setAwayNotification: (msg) => set({ awayNotification: msg }),
  setAgents: (agents) => set({ agents }),
  setIntegrations: (integrations) => set({ integrations }),
  setPivotBlurredNodes: (ids) => set({ pivotBlurredNodes: ids }),
  setJournalOpen: (open) => set({ journalOpen: open }),
  setExportOpen: (open) => set({ exportOpen: open }),
  setSettingsOpen: (open) => set({ settingsOpen: open }),
  setOnboardingOpen: (open) => set({ onboardingOpen: open }),
  setIntegrationDialogId: (id) => set({ integrationDialogId: id }),
  setHasChatted: (value) => set({ hasChatted: value }),
  setHasExported: (value) => set({ hasExported: value }),
  setOrchestratorMessages: (messages) => set({ orchestratorMessages: messages }),
  appendOrchestratorMessage: (message) =>
    set((s) => ({ orchestratorMessages: [...s.orchestratorMessages, message] })),
  setVoiceState: (state) => set({ voiceState: state }),
  setOrbExpanded: (expanded) => set({ orbExpanded: expanded }),
  resetToHome: () => {
    resetVoiceSession()
    set({
      phase: 'intake',
      workspace: null,
      selectedNodeId: null,
      todayPriority: DEFAULT_TODAY_PRIORITY,
      notifications: [],
      healthScore: 0,
      awayNotification: '',
      agents: [{ id: 'orchestrator', name: 'Orchestrator', status: 'active' }],
      integrations: INTEGRATION_CATALOG.map((i) => ({ ...i })),
      projects: [],
      pivotBlurredNodes: [],
      journalOpen: false,
      exportOpen: false,
      settingsOpen: false,
      onboardingOpen: false,
      integrationDialogId: null,
      hasChatted: false,
      hasExported: false,
      orchestratorMessages: [],
      voiceState: 'idle',
      orbExpanded: false,
    })
  },
  getSelectedNode: () => {
    const { workspace, selectedNodeId } = get()
    if (!workspace || !selectedNodeId) return null
    return workspace.nodes.find((n) => n.node_id === selectedNodeId) ?? null
  },
}))
