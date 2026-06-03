import { ReactFlowProvider } from '@xyflow/react'
import { useWorkspaceStore } from './store/workspaceStore'
import { IdeaInput } from './components/intake/IdeaInput'
import { TopBar } from './components/bars/TopBar'
import { NotificationBar } from './components/bars/NotificationBar'
import { ActionBar } from './components/bars/ActionBar'
import { LeftRail } from './components/panels/LeftRail'
import { RightPanel } from './components/panels/RightPanel'
import { StartupCanvas } from './components/canvas/StartupCanvas'

function Dashboard() {
  return (
    <div className="flex h-full flex-col">
      <TopBar />
      <NotificationBar />
      <div className="flex min-h-0 flex-1">
        <LeftRail />
        <main className="min-w-0 flex-1">
          <ReactFlowProvider>
            <StartupCanvas />
          </ReactFlowProvider>
        </main>
        <RightPanel />
      </div>
      <ActionBar />
    </div>
  )
}

function App() {
  const phase = useWorkspaceStore((s) => s.phase)

  if (phase === 'intake') {
    return <IdeaInput />
  }

  return <Dashboard />
}

export default App
