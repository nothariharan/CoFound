import { useState } from 'react'
import { Bot, Check, MoreHorizontal } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspace } from '@/hooks/useWorkspace'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function ActionBar() {
  const { todayPriority, setTodayPriority, workspace, setExportOpen, setSelectedNodeId } = useWorkspaceStore()
  const { fetchPriority, handoffToOrchestrator } = useAgentActions()
  const { fetchWorkspace } = useWorkspace()
  const [refreshing, setRefreshing] = useState(false)
  const [handingOff, setHandingOff] = useState(false)
  const [handoffError, setHandoffError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const stageReady = ['revenue', 'product_vision', 'tech_stack'].every(
    (type) => (workspace?.nodes.find((node) => node.type === type)?.confidence ?? 0) >= 70,
  )

  const handleMarkDone = async () => {
    if (!workspace?.idea_id) return
    setRefreshing(true)
    try {
      const next = await fetchPriority(workspace.idea_id)
      setTodayPriority(next)
    } finally {
      setRefreshing(false)
    }
  }

  const handleHandoff = async () => {
    if (!workspace?.idea_id) return
    setHandingOff(true)
    setHandoffError(null)
    setMenuOpen(false)
    try {
      await handoffToOrchestrator(workspace.idea_id)
      await fetchWorkspace(workspace.idea_id)
      setSelectedNodeId(null)
    } catch (error) {
      setHandoffError(error instanceof Error ? error.message : 'Failed to hand off to orchestrator')
    } finally {
      setHandingOff(false)
    }
  }

  const targetNode = todayPriority.nodeId
    ? workspace?.nodes.find((node) => node.node_id === todayPriority.nodeId)
    : workspace?.nodes.find((node) => node.type === todayPriority.nodeType)
  const canHandoff = Boolean(workspace?.idea_id && targetNode && targetNode.status !== 'locked' && targetNode.active_agents.length === 0)

  return (
    <footer
      className="shell-panel flex min-h-12 shrink-0 items-center justify-between gap-4 border-t border-border bg-card px-4 py-2.5"
      data-onboarding="priority"
    >
      <div className="min-w-0 flex-1">
        <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
          Today&apos;s Priority
          {todayPriority.estimatedTime ? (
            <span className="ml-2 font-normal normal-case tracking-normal">
              · ~{todayPriority.estimatedTime}
            </span>
          ) : null}
        </p>
        <p className="truncate text-sm font-medium text-foreground">{todayPriority.action}</p>
        {todayPriority.reason ? (
          <p className="mt-0.5 hidden truncate text-xs text-muted-foreground md:block">{todayPriority.reason}</p>
        ) : null}
      </div>

      <div className="relative flex shrink-0 items-center gap-2">
        {handoffError && (
          <span className="hidden max-w-[180px] truncate text-xs text-destructive lg:inline">{handoffError}</span>
        )}

        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => void handleMarkDone()}
          disabled={refreshing || !workspace}
        >
          <Check className="size-3.5" />
          {refreshing ? 'Updating…' : 'Done'}
        </Button>

        <Button
          variant="default"
          size="sm"
          onClick={() => setExportOpen(true)}
          disabled={!workspace || !stageReady}
        >
          Export
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="size-8 text-muted-foreground"
          aria-label="More actions"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <MoreHorizontal className="size-4" />
        </Button>

        {menuOpen && (
          <>
            <button
              type="button"
              className="fixed inset-0 z-40 cursor-default"
              aria-label="Close menu"
              onClick={() => setMenuOpen(false)}
            />
            <div className="absolute right-0 bottom-full z-50 mb-2 w-56 overflow-hidden rounded-md border border-border bg-popover shadow-lg">
              <button
                type="button"
                disabled={handingOff || !canHandoff}
                onClick={() => void handleHandoff()}
                className={cn(
                  'flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm transition-colors',
                  canHandoff && !handingOff
                    ? 'text-foreground hover:bg-accent'
                    : 'cursor-not-allowed text-muted-foreground',
                )}
              >
                <Bot className="size-3.5 shrink-0" />
                {handingOff ? 'Handing off…' : 'Handoff to Orchestrator'}
              </button>
            </div>
          </>
        )}
      </div>
    </footer>
  )
}
