import { useWorkspaceStore } from '@/store/workspaceStore'

export function NotificationBar() {
  const { awayNotification } = useWorkspaceStore()

  if (!awayNotification) return null

  return (
    <div className="shell-panel shrink-0 border-b border-border bg-surface-elevated px-4 py-2">
      <p className="text-xs text-muted-foreground">
        <span className="font-medium text-foreground">While you were away:</span>{' '}
        {awayNotification.replace('While you were away: ', '')}
      </p>
    </div>
  )
}
