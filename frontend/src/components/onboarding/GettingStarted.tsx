import { useEffect, useMemo, useState } from 'react'
import { Check, ChevronRight, X } from 'lucide-react'
import { useSSEFeed } from '@/hooks/useSSEFeed'
import { setOnboardingDismissed } from '@/config/storage'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type StepId =
  | 'idea'
  | 'research'
  | 'github'
  | 'posthog'
  | 'chat'
  | 'export'

interface Step {
  id: StepId
  title: string
  description: string
  cta?: string
  action?: () => void
}

export function GettingStarted() {
  const {
    onboardingOpen,
    setOnboardingOpen,
    workspace,
    mode,
    integrations,
    hasChatted,
    hasExported,
    setExportOpen,
    setSelectedNodeId,
    setIntegrationDialogId,
  } = useWorkspaceStore()
  const { messages } = useSSEFeed(workspace?.idea_id)
  const [coachMark, setCoachMark] = useState<string | null>(null)

  const githubConnected = integrations.find((i) => i.id === 'github')?.connected ?? false
  const posthogConnected = integrations.find((i) => i.id === 'posthog')?.connected ?? false
  const researchActive =
    messages.length > 0 ||
    (workspace?.nodes.some((n) => n.confidence > 0 && n.type !== 'core_idea') ?? false)

  const completed = useMemo(
    () => ({
      idea: !!workspace,
      research: researchActive,
      github: githubConnected,
      posthog: posthogConnected,
      chat: hasChatted,
      export: hasExported,
    }),
    [workspace, researchActive, githubConnected, posthogConnected, hasChatted, hasExported],
  )

  const steps: Step[] = [
    {
      id: 'idea',
      title: 'Capture your core idea',
      description: 'Your workspace is created from your initial goal.',
    },
    {
      id: 'research',
      title: 'Let agents research your idea',
      description: 'Watch the agent feed — nodes unlock as confidence grows.',
      cta: 'View canvas',
      action: () => {
        setCoachMark('canvas')
        document.querySelector('[data-onboarding="canvas"]')?.scrollIntoView({ behavior: 'smooth' })
      },
    },
    {
      id: 'github',
      title: 'Connect GitHub',
      description: 'Link your repo to unlock the Build node and track commits.',
      cta: 'Connect GitHub',
      action: () => {
        setCoachMark('integrations')
        setIntegrationDialogId('github')
      },
    },
    {
      id: 'posthog',
      title: 'Connect PostHog',
      description: 'Add analytics to unlock the Observe node and monitor funnel drops.',
      cta: 'Connect PostHog',
      action: () => {
        setCoachMark('integrations')
        setIntegrationDialogId('posthog')
      },
    },
    {
      id: 'chat',
      title: 'Chat with a node',
      description: 'Ask questions or type "pivot" to re-research affected areas.',
      cta: 'Open chat',
      action: () => {
        const core = workspace?.nodes.find((n) => n.type === 'core_idea')
        if (core) setSelectedNodeId(core.node_id)
        setCoachMark('chat')
      },
    },
    {
      id: 'export',
      title: 'Export your blueprint',
      description: 'Download README, tech stack, and handoff docs when ready.',
      cta: 'Export workspace',
      action: () => setExportOpen(true),
    },
  ]

  const doneCount = steps.filter((s) => completed[s.id]).length

  useEffect(() => {
    if (!onboardingOpen || mode !== 'live') return
    const timer = window.setTimeout(() => setCoachMark('priority'), 1200)
    return () => window.clearTimeout(timer)
  }, [onboardingOpen, mode])

  const handleDismiss = () => {
    if (workspace?.idea_id) setOnboardingDismissed(workspace.idea_id)
    setOnboardingOpen(false)
    setCoachMark(null)
  }

  if (!onboardingOpen || mode !== 'live') return null

  return (
    <>
      <div className="fixed bottom-20 right-4 z-50 w-[320px] rounded-xl border border-border bg-card shadow-xl">
        <div className="flex items-start justify-between border-b border-border p-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-primary">Getting started</p>
            <h3 className="mt-1 text-sm font-semibold text-foreground">
              {doneCount} of {steps.length} complete
            </h3>
          </div>
          <Button variant="ghost" size="icon" className="size-7" onClick={handleDismiss} aria-label="Dismiss">
            <X className="size-4" />
          </Button>
        </div>
        <div className="max-h-[360px] overflow-y-auto p-3">
          <div className="flex flex-col gap-2">
            {steps.map((step) => {
              const done = completed[step.id]
              return (
                <div
                  key={step.id}
                  className={cn(
                    'rounded-lg border px-3 py-2.5',
                    done ? 'border-status-validated/30 bg-status-validated/5' : 'border-border',
                  )}
                >
                  <div className="flex items-start gap-2">
                    <div
                      className={cn(
                        'mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full border',
                        done ? 'border-status-validated bg-status-validated text-primary-foreground' : 'border-border',
                      )}
                    >
                      {done && <Check className="size-2.5" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-foreground">{step.title}</p>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">{step.description}</p>
                      {!done && step.cta && step.action && (
                        <Button
                          variant="link"
                          size="sm"
                          className="mt-1 h-auto gap-1 p-0 text-[11px] text-primary"
                          onClick={step.action}
                        >
                          {step.cta}
                          <ChevronRight className="size-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {coachMark && (
        <div className="pointer-events-none fixed inset-0 z-40">
          {coachMark === 'canvas' && (
            <CoachMark
              label="Your startup graph grows here as agents research"
              className="left-[240px] top-24"
            />
          )}
          {coachMark === 'integrations' && (
            <CoachMark
              label="Click GitHub or PostHog to connect and unlock nodes"
              className="left-4 top-[280px]"
            />
          )}
          {coachMark === 'chat' && (
            <CoachMark
              label="Use chat to refine nodes or trigger a pivot"
              className="right-4 top-24"
            />
          )}
          {coachMark === 'priority' && (
            <CoachMark
              label="Today's priority updates as your graph evolves"
              className="bottom-16 left-1/2 -translate-x-1/2"
            />
          )}
        </div>
      )}
    </>
  )
}

function CoachMark({ label, className }: { label: string; className?: string }) {
  return (
    <div
      className={cn(
        'absolute max-w-xs rounded-lg border border-primary/40 bg-card px-3 py-2 text-xs text-foreground shadow-lg',
        className,
      )}
    >
      <span className="font-medium text-primary">Tip:</span> {label}
    </div>
  )
}
