import type { FeedMessage } from '@/types'
import { useWorkspaceStore } from '@/store/workspaceStore'
import {
  createCoreIdeaOnly,
  createStage2Workspace,
  MOCK_FEED_SEQUENCE,
} from '@/mock/workspace'

type DemoCallback = () => void

let timers: ReturnType<typeof setTimeout>[] = []
let feedListeners: Set<(msg: FeedMessage) => void> = new Set()

function clearTimers() {
  timers.forEach(clearTimeout)
  timers = []
}

function schedule(fn: DemoCallback, delay: number) {
  const id = setTimeout(fn, delay)
  timers.push(id)
}

export function subscribeFeed(listener: (msg: FeedMessage) => void) {
  feedListeners.add(listener)
  return () => feedListeners.delete(listener)
}

function emitFeed(msg: FeedMessage) {
  feedListeners.forEach((l) => l(msg))
}

export function startDemoSequence() {
  clearTimers()
  const store = useWorkspaceStore.getState()

  store.setWorkspace(createCoreIdeaOnly())
  store.setPhase('dashboard')
  store.setHealthScore(42)
  store.setDemoStage(1)

  schedule(() => {
    store.setWorkspace(createStage2Workspace())
    store.setHealthScore(64)
    store.setDemoStage(2)
    store.setSelectedNodeId('node-market')
  }, 2500)

  MOCK_FEED_SEQUENCE.forEach(({ delay, message }) => {
    schedule(() => emitFeed(message), delay + 2500)
  })

  schedule(() => {
    store.setTodayPriority({
      action: 'Talk to 3 restaurant owners',
      reason: 'Audience confidence is 72% — this is the highest ROI action today',
      estimatedTime: '2 hrs',
      impact: 'High impact',
    })
  }, 7000)
}

export function triggerPivotDemo() {
  const store = useWorkspaceStore.getState()
  store.setPivotBlurredNodes(['node-audience', 'node-competitors'])
  emitFeed({
    text: '[Diff Classifier] Diff identified. Re-researching Audience and Competitors...',
    type: 'info',
  })

  schedule(() => {
    store.setPivotBlurredNodes([])
    const ws = createStage2Workspace()
    ws.nodes = ws.nodes.map((n) => {
      if (n.node_id === 'node-audience') {
        return { ...n, confidence: 78, summary: 'Ghost kitchen operators — B2B pivot segment', last_updated: new Date().toISOString() }
      }
      if (n.node_id === 'node-competitors') {
        return { ...n, confidence: 65, summary: 'CloudKitchens, Kitchen United — B2B landscape', last_updated: new Date().toISOString() }
      }
      return n
    })
    store.setWorkspace(ws)
    emitFeed({ text: '[Orchestrator] Pivot complete. Audience and Competitors updated.', type: 'done' })
  }, 3000)
}

export function stopDemoSequence() {
  clearTimers()
  feedListeners.clear()
}

export async function mockCreateWorkspace(_idea: string) {
  await new Promise((r) => setTimeout(r, 800))
  startDemoSequence()
  return useWorkspaceStore.getState().workspace!
}

export async function mockFetchWorkspace(_ideaId: string) {
  await new Promise((r) => setTimeout(r, 400))
  return createStage2Workspace()
}
