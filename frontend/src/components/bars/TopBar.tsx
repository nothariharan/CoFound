import { useWorkspaceStore } from '../../store/workspaceStore'

export function TopBar() {
  const { workspace } = useWorkspaceStore()
  const score = workspace?.nodes.length
    ? Math.round(
        workspace.nodes.reduce((sum, n) => sum + n.confidence, 0) /
          workspace.nodes.length,
      )
    : 0

  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-[#e5e5e5] bg-white px-4">
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold text-[#171717]">CoFounder</span>
        <span className="text-[#e5e5e5]">·</span>
        <span className="text-sm text-[#737373]">
          {workspace?.workspace_name ?? 'Workspace'}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-xs text-[#737373]">
          Health <span className="font-medium text-[#171717]">{score}/100</span>
        </span>
      </div>
    </header>
  )
}
