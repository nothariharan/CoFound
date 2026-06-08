import { useEffect } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import { WORKSPACE_KEY, getOnboardingDismissed } from '@/config/storage'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useShellEntrance } from '@/hooks/useAnimations'
import { IdeaInput } from '@/components/intake/IdeaInput'
import { TopBar } from '@/components/bars/TopBar'
import { NotificationBar } from '@/components/bars/NotificationBar'
import { ActionBar } from '@/components/bars/ActionBar'
import { LeftRail } from '@/components/panels/LeftRail'
import { RightPanel } from '@/components/panels/RightPanel'
import { StartupCanvas } from '@/components/canvas/StartupCanvas'
import { DecisionJournal } from '@/components/journal/DecisionJournal'
import { ExportModal } from '@/components/export/ExportModal'
import { GettingStarted } from '@/components/onboarding/GettingStarted'

function Dashboard() {
  const shellRef = useShellEntrance()
  const { workspace, mode, setOnboardingOpen } = useWorkspaceStore()

  useEffect(() => {
    if (mode !== 'live' || !workspace?.idea_id) return
    if (!getOnboardingDismissed(workspace.idea_id)) {
      setOnboardingOpen(true)
    }
  }, [workspace?.idea_id, mode, setOnboardingOpen])

  return (
    <div ref={shellRef} className="flex h-dvh flex-col">
      <TopBar />
      <NotificationBar />
      <div className="flex min-h-0 flex-1">
        <LeftRail />
        <main className="relative min-h-0 min-w-0 flex-1" data-onboarding="canvas">
          <ReactFlowProvider>
            <div className="size-full min-h-0">
              <StartupCanvas />
            </div>
          </ReactFlowProvider>
        </main>
        <RightPanel />
      </div>
      <ActionBar />
      <DecisionJournal />
      <ExportModal />
      <GettingStarted />
    </div>
  )
}

function App() {
  const phase = useWorkspaceStore((s) => s.phase)
  const workspace = useWorkspaceStore((s) => s.workspace)
  const mode = useWorkspaceStore((s) => s.mode)

  useEffect(() => {
    if (mode !== 'live' || !workspace?.idea_id) return
    localStorage.setItem(WORKSPACE_KEY, workspace.idea_id)
  }, [workspace?.idea_id, mode])

  if (phase === 'intake') {
    return <IdeaInput />
  }

  return <Dashboard />
}

export default App
