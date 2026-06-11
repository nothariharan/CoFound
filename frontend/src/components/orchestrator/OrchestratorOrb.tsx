import { useEffect, useRef, useState } from 'react'
import { Mic, MicOff, Send, X } from 'lucide-react'
import { useVoiceOrchestrator } from '@/hooks/useVoiceOrchestrator'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

function OrchestratorMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-hidden>
      <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="1.5" opacity="0.35" />
      <circle cx="24" cy="24" r="6" fill="currentColor" />
      <circle cx="24" cy="8" r="3" fill="currentColor" opacity="0.85" />
      <circle cx="38" cy="30" r="3" fill="currentColor" opacity="0.85" />
      <circle cx="10" cy="30" r="3" fill="currentColor" opacity="0.85" />
      <path
        d="M24 11v7M34.5 28.5l-6-3.5M13.5 28.5l6-3.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.7"
      />
    </svg>
  )
}

const voiceLabels = {
  idle: 'Tap to talk',
  listening: 'Listening… tap to send',
  transcribing: 'Transcribing…',
  thinking: 'Thinking…',
  speaking: 'Speaking…',
} as const

export function OrchestratorOrb() {
  const { messages, voiceState, toggleListening, sendMessage } = useVoiceOrchestrator()
  const { orbExpanded, setOrbExpanded } = useWorkspaceStore()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, orbExpanded])

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!input.trim()) return
    const text = input.trim()
    setInput('')
    await sendMessage(text, { speak: false })
  }

  return (
    <div className="pointer-events-none absolute inset-0 z-30">
      {orbExpanded && (
        <button
          type="button"
          className="pointer-events-auto absolute inset-0 bg-background/20 backdrop-blur-[1px]"
          aria-label="Close orchestrator overlay"
          onClick={() => setOrbExpanded(false)}
        />
      )}

      <div
        className={cn(
          'pointer-events-auto absolute right-5 bottom-24 flex flex-col items-end gap-3',
          orbExpanded && 'bottom-28',
        )}
      >
        {orbExpanded && (
          <div className="w-[min(92vw,340px)] overflow-hidden rounded-2xl border border-border bg-card/95 shadow-2xl backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-foreground">Orchestrator</p>
                <p className="text-[11px] text-muted-foreground">{voiceLabels[voiceState]}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => setOrbExpanded(false)}
                aria-label="Collapse"
              >
                <X className="size-4" />
              </Button>
            </div>

            <ScrollArea className="max-h-[220px]">
              <div className="flex flex-col gap-3 p-4">
                {messages.slice(-4).map((msg, index) => (
                  <div
                    key={`${msg.text}-${index}`}
                    className={cn('flex flex-col gap-1', msg.role === 'user' && 'items-end')}
                  >
                    <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                      {msg.role === 'user' ? 'You' : (msg.agentName ?? 'Orchestrator')}
                    </span>
                    <div
                      className={cn(
                        'max-w-[92%] rounded-lg px-3 py-2 text-xs leading-relaxed',
                        msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground/90',
                      )}
                    >
                      {msg.text}
                    </div>
                    {msg.actionsTaken?.length ? (
                      <div className="flex flex-wrap gap-1">
                        {msg.actionsTaken.map((action) => (
                          <Badge key={action.summary} variant="outline" className="text-[10px]">
                            {action.summary}
                          </Badge>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            </ScrollArea>

            <form onSubmit={(e) => void handleSend(e)} className="border-t border-border p-3">
              <div className="flex items-end gap-2">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Or type a command…"
                  rows={2}
                  className="min-h-[52px] resize-none text-xs"
                  disabled={voiceState === 'thinking' || voiceState === 'transcribing'}
                />
                <Button type="submit" size="icon" disabled={!input.trim()} aria-label="Send">
                  <Send className="size-4" />
                </Button>
              </div>
            </form>
          </div>
        )}

        <div className="flex items-center gap-3">
          {orbExpanded && (
            <Button
              type="button"
              variant={voiceState === 'listening' ? 'default' : 'outline'}
              size="sm"
              className="gap-2 shadow-lg"
              onClick={() => void toggleListening()}
              disabled={voiceState === 'thinking' || voiceState === 'transcribing' || voiceState === 'speaking'}
            >
              {voiceState === 'listening' ? <MicOff className="size-4" /> : <Mic className="size-4" />}
              {voiceState === 'listening' ? 'Stop' : 'Mic'}
            </Button>
          )}

          <button
            type="button"
            onClick={() => setOrbExpanded(!orbExpanded)}
            className={cn(
              'relative flex size-16 items-center justify-center rounded-full border border-primary/40 bg-card/90 text-primary shadow-xl backdrop-blur-md transition-all hover:scale-105',
              voiceState === 'listening' && 'animate-pulse ring-4 ring-primary/30',
              voiceState === 'thinking' && 'ring-4 ring-primary/20',
              voiceState === 'speaking' && 'ring-4 ring-status-validated/40',
            )}
            aria-label={orbExpanded ? 'Orchestrator menu' : 'Open orchestrator'}
          >
            <OrchestratorMark className="size-9" />
            <span
              className={cn(
                'absolute -top-1 -right-1 size-3 rounded-full border-2 border-card',
                voiceState === 'idle' && 'bg-muted-foreground',
                voiceState === 'listening' && 'bg-destructive',
                voiceState === 'transcribing' && 'bg-status-needs-work',
                voiceState === 'thinking' && 'bg-primary',
                voiceState === 'speaking' && 'bg-status-validated',
              )}
            />
          </button>
        </div>
      </div>
    </div>
  )
}
