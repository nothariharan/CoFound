import { useRef, useState } from 'react'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useIntakeAnimation } from '@/hooks/useAnimations'
import { clearSavedWorkspaceId, getSavedWorkspaceId } from '@/config/storage'
import { AppCursorProvider } from '@/components/cursor/AppCursorProvider'
import { Button } from '@/components/ui/button'
import AnimatedGradientBackground from '@/components/ui/animated-gradient-background'
import { AgentCursors } from '@/components/intake/AgentCursors'
import { CoFoundLogo } from '@/components/intake/OrbitalDiagram'

import { AgentWorkGallery } from '@/components/intake/AgentWorkGallery'

const BRANDED_GRADIENT = {
  gradientColors: ['#c96442', '#8a4733', '#3a241a', '#161311', '#0c0c0b', '#0a0a09'],
  gradientStops: [12, 32, 52, 70, 86, 100],
  startingGap: 130,
  breathingRange: 6,
  animationSpeed: 0.02,
  Breathing: true,
  topOffset: 0,
}

export function IdeaInput() {
  const [idea, setIdea] = useState('')
  const [resuming, setResuming] = useState(false)
  const [framing, setFraming] = useState(false)
  const { createWorkspace, fetchWorkspace, loading, error } = useWorkspace()
  const containerRef = useIntakeAnimation()
  const formRef = useRef<HTMLFormElement>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!idea.trim() || loading) return
    setFraming(true)
    try {
      await Promise.all([
        createWorkspace(idea.trim()),
        new Promise((resolve) => window.setTimeout(resolve, 900)),
      ])
    } finally {
      setFraming(false)
    }
  }

  const handleGetStarted = async () => {
    const savedId = getSavedWorkspaceId()
    if (savedId) {
      setResuming(true)
      try {
        await fetchWorkspace(savedId)
        return
      } catch {
        clearSavedWorkspaceId()
      } finally {
        setResuming(false)
      }
    }
    formRef.current?.querySelector<HTMLInputElement>('input')?.focus()
  }

  return (
    <AppCursorProvider>
    <div
      ref={containerRef}
      className="landing-page relative flex min-h-dvh flex-col overflow-x-hidden bg-background"
    >
      <div className="pointer-events-none fixed inset-0 z-0">
        <AnimatedGradientBackground {...BRANDED_GRADIENT} />
      </div>

      <AgentCursors targetRef={formRef} />

      <header className="intake-nav relative z-40 mx-auto flex w-full max-w-5xl items-center justify-between px-6 pt-8 md:px-10">
        <div className="flex items-center gap-3">
          <CoFoundLogo markClassName="size-8 text-foreground md:size-9" />
          <span className="text-lg font-semibold tracking-tight text-foreground md:text-xl">CoFound</span>
        </div>
        <div className="flex items-center gap-3">
          <Button
            type="button"
            onClick={handleGetStarted}
            disabled={loading || resuming}
            className="intake-nav-btn h-9 rounded-lg bg-primary px-4 text-sm text-primary-foreground hover:bg-primary/90"
          >
            {resuming ? 'Opening...' : 'Get started'}
          </Button>
        </div>
      </header>

      <main className="relative z-30 mx-auto flex w-full max-w-6xl flex-1 flex-col items-center px-6 pb-4 pt-8 md:px-10">
        <div className="hero-center-stack relative flex w-full flex-col items-center">
          <div className="intake-logo-watermark pointer-events-none absolute left-1/2 top-1/2 z-0 -translate-x-1/2 -translate-y-1/2" aria-hidden>
            <CoFoundLogo markClassName="hero-watermark-mark size-[240px] text-primary opacity-[0.08] md:size-[320px]" />
          </div>

          <div className="relative z-10 flex w-full flex-col items-center">
            <div className="intake-hero-badge mb-6 rounded-full border border-primary/30 bg-card/60 px-4 py-1.5 backdrop-blur-sm">
              <span className="text-[10px] font-medium uppercase tracking-[0.2em] text-primary">
                AI Founder Operating System
              </span>
            </div>

            <h1 className="intake-hero-title font-display mb-4 max-w-2xl text-center text-4xl leading-[1.05] tracking-[-0.03em] md:text-[3.25rem]">
              Your AI Co-Founder for every step of your{' '}
              <span className="text-white">journey</span>
            </h1>

            <p className="intake-hero-sub mb-10 max-w-xl text-center text-base leading-relaxed">
              Specialized research agents work in parallel — researching markets, validating
              assumptions, building your product, and scaling growth — all from your single idea.
            </p>

            {framing && (
              <div className="mb-4 rounded-lg border border-primary/30 bg-card/70 px-4 py-3 text-center text-sm text-foreground backdrop-blur-sm">
                Framing your startup, naming the workspace, and preparing the first decision point...
              </div>
            )}

            <form
              ref={formRef}
              onSubmit={handleSubmit}
              className="intake-input-shell mb-4 w-full max-w-2xl"
            >
              <div className="flex items-center gap-3 rounded-xl border border-border bg-card/80 p-2 pl-4 backdrop-blur-sm">
                <svg viewBox="0 0 16 16" className="size-4 shrink-0 text-primary" aria-hidden>
                  <path
                    d="M8 1l1.5 3.5L13 6l-3.5 1.5L8 11 6.5 7.5 3 6l3.5-1.5L8 1Z"
                    fill="currentColor"
                  />
                </svg>
                <input
                  type="text"
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  placeholder="Describe your startup idea in a sentence or two..."
                  className="min-w-0 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
                  autoFocus
                />
                <Button
                  type="submit"
                  disabled={!idea.trim() || loading || framing}
                  className="h-10 shrink-0 gap-2 rounded-lg bg-primary px-5 text-sm text-primary-foreground hover:bg-primary/90"
                >
                  {loading || framing ? 'Framing...' : 'Continue'}
                  {!loading && !framing && (
                    <svg viewBox="0 0 16 16" className="size-4" aria-hidden>
                      <path
                        d="M3 8h10M9 4l4 4-4 4"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </Button>
              </div>
              {error && <p className="mt-3 text-center text-sm text-destructive">{error}</p>}
            </form>
          </div>
        </div>

        <AgentWorkGallery className="mt-8 w-full max-w-none pb-6 md:mt-12" />
      </main>
    </div>
    </AppCursorProvider>
  )
}
