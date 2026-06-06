import { Bell, Clock } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function TopBar() {
  const { workspace, healthScore } = useWorkspaceStore()
  const score = healthScore || (workspace?.nodes.length
    ? Math.round(workspace.nodes.reduce((sum, n) => sum + n.confidence, 0) / workspace.nodes.length)
    : 0)

  const healthColor =
    score >= 70 ? 'bg-status-validated' : score >= 50 ? 'bg-status-needs-work' : 'bg-status-blocking'

  return (
    <header className="shell-panel flex h-12 shrink-0 items-center justify-between border-b border-border bg-card px-4">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-foreground">CoFound</span>
        <span className="h-3 w-px bg-border" aria-hidden />
        <span className="text-sm text-muted-foreground">{workspace?.workspace_name ?? 'Workspace'}</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-md bg-surface-elevated px-2 py-0.5">
          <span className="text-xs text-muted-foreground">Startup Health</span>
          <span className="text-sm font-medium tabular-nums text-foreground">{score}</span>
          <span className="text-xs text-muted-foreground">/ 100</span>
          <span className={cn('size-2 rounded-full', healthColor)} aria-label="Health status" />
        </div>

        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="size-8 text-muted-foreground" aria-label="Notifications">
            <Bell className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" className="size-8 text-muted-foreground" aria-label="History">
            <Clock className="size-4" />
          </Button>
          <Avatar className="size-7">
            <AvatarFallback className="bg-surface-elevated text-[10px] text-foreground">AK</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}
