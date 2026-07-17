import { Compass } from 'lucide-react'
import { useGoHome } from '@/hooks/useGoHome'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function workspaceInitials(name?: string | null) {
  if (!name?.trim()) return 'CF'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0]![0] ?? ''}${parts[1]![0] ?? ''}`.toUpperCase()
  }
  return name.trim().slice(0, 2).toUpperCase()
}

export function TopBar() {
  const goHome = useGoHome()
  const { workspace, healthScore, setOnboardingOpen } = useWorkspaceStore()
  const score = healthScore || (workspace?.nodes.length
    ? Math.round(workspace.nodes.reduce((sum, n) => sum + n.confidence, 0) / workspace.nodes.length)
    : 0)

  const healthColor =
    score >= 70 ? 'bg-status-validated' : score >= 50 ? 'bg-status-needs-work' : 'bg-status-blocking'

  const initials = workspaceInitials(workspace?.workspace_name)

  return (
    <header className="shell-panel flex h-12 shrink-0 items-center justify-between border-b border-border bg-card px-4">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={goHome}
          className="shrink-0 text-sm font-medium text-foreground transition-colors hover:text-primary"
        >
          CoFound
        </button>
        <span className="h-3 w-px shrink-0 bg-border" aria-hidden />
        <span className="truncate text-sm text-muted-foreground">
          {workspace?.workspace_name ?? 'Workspace'}
        </span>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <div className="flex items-center gap-2 rounded-md bg-surface-elevated px-2.5 py-1">
          <span className="hidden text-xs text-muted-foreground sm:inline">Health</span>
          <span className="text-sm font-medium tabular-nums text-foreground">{score}</span>
          <span className={cn('size-2 rounded-full', healthColor)} aria-label="Health status" />
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="size-8 text-muted-foreground"
          onClick={() => setOnboardingOpen(true)}
          aria-label="Open guide"
        >
          <Compass className="size-4" />
        </Button>

        <Avatar className="size-7">
          <AvatarFallback className="bg-surface-elevated text-[10px] text-foreground">
            {initials}
          </AvatarFallback>
        </Avatar>
      </div>
    </header>
  )
}
