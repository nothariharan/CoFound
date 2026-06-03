import { useWorkspaceStore } from '../store/workspaceStore'

export function useAgents() {
  const workspace = useWorkspaceStore((s) => s.workspace)

  const activeAgents = workspace?.nodes.flatMap((n) =>
    n.active_agents.map((agent) => ({ agent, nodeId: n.node_id, nodeTitle: n.title })),
  ) ?? []

  return {
    activeAgents,
    count: activeAgents.length,
  }
}
