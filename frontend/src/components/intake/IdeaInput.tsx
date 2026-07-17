import { useEffect, useRef, useState } from 'react'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useIntakeAnimation } from '@/hooks/useAnimations'
import { clearSavedWorkspaceId, getSavedWorkspaceId } from '@/config/storage'
import { AppCursorProvider } from '@/components/cursor/AppCursorProvider'
import { Button } from '@/components/ui/button'
import AnimatedGradientBackground from '@/components/ui/animated-gradient-background'
import { AgentCursors } from '@/components/intake/AgentCursors'
import { CoFoundLogo } from '@/components/intake/OrbitalDiagram'

import { AgentWorkGallery } from '@/components/intake/AgentWorkGallery'
import { ApiError, apiFetch, warmApi } from '@/lib/api'

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
  const [inputPulsing, setInputPulsing] = useState(false)
  const [sessionExpired, setSessionExpired] = useState(false)
  const [resumeHint, setResumeHint] = useState<string | null>(null)
  const [backendStatus, setBackendStatus] = useState<'checking' | 'ready' | 'unavailable'>('checking')
  const [hasSavedWorkspace, setHasSavedWorkspace] = useState(() => Boolean(getSavedWorkspaceId()))
  const { createWorkspace, fetchWorkspace, loading, error } = useWorkspace()
  const containerRef = useIntakeAnimation()
  const formRef = useRef<HTMLFormElement>(null)

  useEffect(() => {
    let cancelled = false
    let activeController: AbortController | null = null
    let retryTimer: number | undefined

    const run = async () => {
      if (cancelled) return
      setBackendStatus((prev) => (prev === 'ready' ? prev : 'checking'))
      activeController = new AbortController()
      const ready = await warmApi(activeController.signal)
      if (cancelled) return
      setBackendStatus(ready ? 'ready' : 'unavailable')

      // if we have a saved id, check it still exists so the CTA stays honest
      const savedId = getSavedWorkspaceId()
      if (ready && savedId) {
        try {
          await apiFetch(`/api/workspace/${savedId}`, {
            signal: activeController.signal,
            timeoutMs: 90_000,
          })
          if (!cancelled) setHasSavedWorkspace(true)
        } catch (err) {
          if (cancelled) return
          const status = err instanceof ApiError ? err.status : undefined
          if (status === 404) {
            clearSavedWorkspaceId()
            setHasSavedWorkspace(false)
            setSessionExpired(true)
          }
          // network / cold start — keep the local flag, resume can retry on click
        }
      } else if (!savedId) {
        setHasSavedWorkspace(false)
      }

      // keep nudging a sleeping free-tier box until it answers
      if (!ready) {
        retryTimer = window.setTimeout(() => {
          void run()
        }, 12_000)
      }
    }

    void run()
    return () => {
      cancelled = true
      activeController?.abort()
      if (retryTimer !== undefined) window.clearTimeout(retryTimer)
    }
  }, [])

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!idea.trim() || loading || framing) return
    setFraming(true)
    setSessionExpired(false)
    setResumeHint(null)
    try {
      await Promise.all([
        createWorkspace(idea.trim()),
        new Promise((resolve) => window.setTimeout(resolve, 400)),
      ])
    } finally {
      setFraming(false)
    }
  }

  const openSavedWorkspace = async () => {
    const savedId = getSavedWorkspaceId()
    if (!savedId) {
      setHasSavedWorkspace(false)
      return
    }

    setResuming(true)
    setSessionExpired(false)
    setResumeHint(null)
    try {
      await fetchWorkspace(savedId)
    } catch (err) {
      const status = err instanceof ApiError ? err.status : undefined
      if (status === 404) {
        clearSavedWorkspaceId()
        setHasSavedWorkspace(false)
        setSessionExpired(true)
      } else {
        setResumeHint(
          status === 503 || status === 502 || status === 504
            ? 'The workspace service is waking up. Tap Open workspace again in a moment.'
            : 'Could not reopen your workspace yet. Check your connection and try again.',
        )
        void warmApi().then((ready) => setBackendStatus(ready ? 'ready' : 'unavailable'))
      }
    } finally {
      setResuming(false)
    }
  }

  const handleGetStarted = async () => {
    if (hasSavedWorkspace || getSavedWorkspaceId()) {
      await openSavedWorkspace()
      return
    }

    if (idea.trim()) {
      await handleSubmit()
      return
    }

    const input = formRef.current?.querySelector<HTMLInputElement>('input')
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    input?.focus()
    setInputPulsing(true)
    window.setTimeout(() => setInputPulsing(false), 700)
  }

  const busy = loading || framing || resuming
  const ctaLabel = resuming
    ? 'Opening…'
    : framing
      ? 'Starting…'
      : hasSavedWorkspace
        ? 'Open workspace'
        : 'Get started'

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
            onClick={() => void handleGetStarted()}
            disabled={busy}
            className="intake-nav-btn h-9 gap-2 rounded-lg bg-primary px-4 text-sm text-primary-foreground hover:bg-primary/90"
          >
            {(resuming || (framing && !idea.trim())) && (
              <span className="size-3.5 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
            )}
            {ctaLabel}
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

            {(framing || resuming) && (
              <div className="mb-4 flex items-center gap-3 rounded-lg border border-primary/30 bg-card/70 px-4 py-3 text-left text-sm text-foreground backdrop-blur-sm" role="status" aria-live="polite">
                <span className="size-4 shrink-0 animate-spin rounded-full border-2 border-primary/25 border-t-primary" />
                <span>
                  <strong className="block font-medium">
                    {resuming ? 'Opening your workspace' : 'Building your workspace'}
                  </strong>
                  <span className="text-xs text-muted-foreground">
                    {resuming
                      ? 'Restoring your graph and latest agent progress…'
                      : 'Framing the idea and preparing your first decision point…'}
                  </span>
                </span>
              </div>
            )}

            {!framing && !resuming && backendStatus === 'checking' && (
              <p className="mb-3 flex items-center gap-2 text-xs text-muted-foreground" role="status">
                <span className="size-3 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground" />
                Connecting to agents…
              </p>
            )}

            {!framing && !resuming && backendStatus === 'unavailable' && (
              <p className="mb-3 text-center text-xs text-amber-200/90" role="status">
                Agents are still waking up — you can type your idea now. Continue will retry automatically.
              </p>
            )}

            {sessionExpired && (
              <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-center text-sm text-amber-200 backdrop-blur-sm">
                Your previous session has expired. Enter a new idea below to start fresh.
              </div>
            )}

            {resumeHint && (
              <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-center text-sm text-amber-200 backdrop-blur-sm">
                {resumeHint}
              </div>
            )}

            <form
              ref={formRef}
              onSubmit={(e) => void handleSubmit(e)}
              className="intake-input-shell mb-4 w-full max-w-2xl"
            >
              <div className={`flex items-center gap-3 rounded-xl border bg-card/80 p-2 pl-4 backdrop-blur-sm transition-all duration-300 ${inputPulsing ? 'border-primary ring-2 ring-primary/50' : 'border-border'}`}>
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
                  disabled={busy}
                />
                <Button
                  type="submit"
                  disabled={!idea.trim() || busy}
                  className="h-10 shrink-0 gap-2 rounded-lg bg-primary px-5 text-sm text-primary-foreground hover:bg-primary/90"
                >
                  {(loading || framing) && (
                    <span className="size-3.5 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                  )}
                  {loading || framing ? 'Framing…' : 'Continue'}
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
              {hasSavedWorkspace && !resuming && !framing && (
                <p className="mt-3 text-center text-xs text-muted-foreground">
                  Already building?{' '}
                  <button
                    type="button"
                    onClick={() => void openSavedWorkspace()}
                    disabled={busy}
                    className="font-medium text-primary underline-offset-2 hover:underline disabled:opacity-60"
                  >
                    Open your last workspace
                  </button>
                </p>
              )}
            </form>
          </div>
        </div>

        <AgentWorkGallery className="mt-10 w-full pb-10 md:mt-14" />
      </main>
    </div>
    </AppCursorProvider>
  )
}
