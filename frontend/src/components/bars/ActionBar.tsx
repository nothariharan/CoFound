import { useState } from 'react'
import { Bot, Check } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspace } from '@/hooks/useWorkspace'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function ActionBar() {
  const { todayPriority, setTodayPriority, workspace, setExportOpen, setSelectedNodeId } = useWorkspaceStore()
  const { fetchPriority, handoffToOrchestrator } = useAgentActions()
  const { fetchWorkspace } = useWorkspace()
  const [refreshing, setRefreshing] = useState(false)
  const [handingOff, setHandingOff] = useState(false)
  const [handoffError, setHandoffError] = useState<string | null>(null)
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
    <footer className="shell-panel flex h-14 shrink-0 items-center justify-between border-t border-border bg-card px-4" data-onboarding="priority">
      <div className="flex items-center gap-6">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Today&apos;s Priority</p>
          <p className="text-sm font-medium text-foreground">{todayPriority.action}</p>
        </div>
        <div className="hidden sm:block max-w-md">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Why</p>
          <p className="text-sm text-muted-foreground">{todayPriority.reason}</p>
        </div>
        <div className="hidden items-center gap-2 md:flex">
          {todayPriority.impact && <Badge variant="warning">{todayPriority.impact}</Badge>}
          {todayPriority.estimatedTime && (
            <span className="text-xs text-muted-foreground">~{todayPriority.estimatedTime}</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {handoffError && <span className="hidden max-w-xs truncate text-xs text-destructive lg:inline">{handoffError}</span>}
        <Button
          variant="secondary"
          size="sm"
          className="gap-2"
          onClick={() => void handleHandoff()}
          disabled={handingOff || !canHandoff}
        >
          <Bot className="size-3.5" />
          {handingOff ? 'Handing off...' : 'Handoff to Orchestrator'}
        </Button>
        <Button variant="outline" size="sm" className="gap-2" onClick={() => void handleMarkDone()} disabled={refreshing || !workspace}>
          <Check className="size-3.5" />
          {refreshing ? 'Updating...' : 'Mark as done'}
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={() => setExportOpen(true)}
          disabled={!workspace || !stageReady}
        >
          Approve & Export
        </Button>
      </div>
    </footer>
  )
}
