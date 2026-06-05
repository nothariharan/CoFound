import { Check } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function ActionBar() {
  const { todayPriority } = useWorkspaceStore()

  return (
    <footer className="shell-panel flex h-14 shrink-0 items-center justify-between border-t border-border bg-card px-4">
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
      <Button variant="default" size="sm" className="gap-2">
        <Check className="size-3.5" />
        Mark as done
      </Button>
    </footer>
  )
}
