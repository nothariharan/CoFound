import { useEffect } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import { getOnboardingDismissed } from '@/config/storage'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useShellEntrance } from '@/hooks/useAnimations'
import { TopBar } from '@/components/bars/TopBar'
import { NotificationBar } from '@/components/bars/NotificationBar'
import { ActionBar } from '@/components/bars/ActionBar'
import { LeftRail } from '@/components/panels/LeftRail'
import { RightPanel } from '@/components/panels/RightPanel'
import { StartupCanvas } from '@/components/canvas/StartupCanvas'
import { DecisionJournal } from '@/components/journal/DecisionJournal'
import { ExportModal } from '@/components/export/ExportModal'
import { GettingStarted } from '@/components/onboarding/GettingStarted'
import { SettingsDialog } from '@/components/settings/SettingsDialog'
import { OrchestratorOrb } from '@/components/orchestrator/OrchestratorOrb'

export default function Dashboard() {
  const shellRef = useShellEntrance()
  const { workspace, setOnboardingOpen, selectedNodeId } = useWorkspaceStore()

  useEffect(() => {
    if (!workspace?.idea_id) return
    if (!getOnboardingDismissed(workspace.idea_id)) {
      setOnboardingOpen(true)
    }
  }, [workspace?.idea_id, setOnboardingOpen])

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
          {/* Orb only when a node is selected — otherwise the right panel is the orchestrator */}
          {selectedNodeId ? <OrchestratorOrb /> : null}
        </main>
        <RightPanel />
      </div>
      <ActionBar />
      <DecisionJournal />
      <ExportModal />
      <SettingsDialog />
      <GettingStarted />
    </div>
  )
}
