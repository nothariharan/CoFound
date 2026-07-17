import { lazy, Suspense, useEffect } from 'react'
import { WORKSPACE_KEY } from '@/config/storage'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { IdeaInput } from '@/components/intake/IdeaInput'

const Dashboard = lazy(() => import('@/components/dashboard/Dashboard'))

function App() {
  const phase = useWorkspaceStore((s) => s.phase)
  const workspace = useWorkspaceStore((s) => s.workspace)

  useEffect(() => {
    if (!workspace?.idea_id) return
    localStorage.setItem(WORKSPACE_KEY, workspace.idea_id)
  }, [workspace?.idea_id])

  if (phase === 'intake') {
    return <IdeaInput />
  }

  return (
    <Suspense fallback={<DashboardLoading />}>
      <Dashboard />
    </Suspense>
  )
}

function DashboardLoading() {
  return (
    <div className="grid h-dvh place-items-center bg-background" role="status" aria-live="polite">
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <span className="size-5 animate-spin rounded-full border-2 border-primary/25 border-t-primary" />
        Opening your workspace…
      </div>
    </div>
  )
}

export default App
