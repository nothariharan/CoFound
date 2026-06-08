import { useState } from 'react'
import { Check } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useAgentActions } from '@/hooks/useAgentActions'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function ActionBar() {
  const { todayPriority, setTodayPriority, workspace } = useWorkspaceStore()
  const { fetchPriority } = useAgentActions()
  const [refreshing, setRefreshing] = useState(false)

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
      <Button variant="default" size="sm" className="gap-2" onClick={() => void handleMarkDone()} disabled={refreshing || !workspace}>
        <Check className="size-3.5" />
        {refreshing ? 'Updating...' : 'Mark as done'}
      </Button>
    </footer>
  )
}
