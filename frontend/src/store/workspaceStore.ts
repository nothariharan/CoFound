import { create } from 'zustand'
import type { AppPhase, GraphNode, TodayPriority, Workspace } from '../types'

interface WorkspaceState {
  phase: AppPhase
  workspace: Workspace | null
  selectedNodeId: string | null
  todayPriority: TodayPriority
  notifications: string[]
  setPhase: (phase: AppPhase) => void
  setWorkspace: (workspace: Workspace) => void
  setSelectedNodeId: (id: string | null) => void
  setTodayPriority: (priority: TodayPriority) => void
  getSelectedNode: () => GraphNode | null
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  phase: 'intake',
  workspace: null,
  selectedNodeId: null,
  todayPriority: {
    action: 'Refine your core idea with more detail',
    reason: 'Core Idea confidence is below validation threshold',
    estimatedTime: '~15 min',
  },
  notifications: [],
  setPhase: (phase) => set({ phase }),
  setWorkspace: (workspace) => set({ workspace, selectedNodeId: workspace.nodes[0]?.node_id ?? null }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setTodayPriority: (priority) => set({ todayPriority: priority }),
  getSelectedNode: () => {
    const { workspace, selectedNodeId } = get()
    if (!workspace || !selectedNodeId) return null
    return workspace.nodes.find((n) => n.node_id === selectedNodeId) ?? null
  },
}))
