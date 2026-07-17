import { useEffect, useState } from 'react'
import { Code2, Lightbulb, LineChart, Search, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'

type JourneyStep = {
  id: string
  title: string
  description: string
  accent: string
  glow: string
  icon: typeof Search
}

const STEPS: JourneyStep[] = [
  {
    id: 'research',
    title: 'Research',
    description: 'Deep market & competitor insights tailored to your idea.',
    accent: '#4a8eff',
    glow: 'rgba(74, 142, 255, 0.35)',
    icon: Search,
  },
  {
    id: 'validate',
    title: 'Validate',
    description: 'Test assumptions, analyze demand, and de-risk your idea.',
    accent: '#5fb87a',
    glow: 'rgba(95, 184, 122, 0.35)',
    icon: Lightbulb,
  },
  {
    id: 'build',
    title: 'Build',
    description: 'Plan, create, and iterate your product with AI guidance.',
    accent: '#8b7cf6',
    glow: 'rgba(139, 124, 246, 0.3)',
    icon: Code2,
  },
  {
    id: 'test',
    title: 'Test & Learn',
    description: 'Run experiments, track metrics, and learn what works.',
    accent: '#c96442',
    glow: 'rgba(201, 100, 66, 0.4)',
    icon: LineChart,
  },
  {
    id: 'grow',
    title: 'Grow',
    description: 'Scale with data-driven strategies and continuous optimization.',
    accent: '#3ecf8e',
    glow: 'rgba(62, 207, 142, 0.35)',
    icon: TrendingUp,
  },
]

type AgentWorkGalleryProps = {
  className?: string
}

export function AgentWorkGallery({ className = '' }: AgentWorkGalleryProps) {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActive((prev) => (prev + 1) % STEPS.length)
    }, 2800)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <section
      aria-label="How CoFound runs your startup loop"
      className={cn('relative z-30 w-full max-w-5xl px-2 md:px-0', className)}
    >
      <div className="founder-loop relative overflow-hidden rounded-2xl border border-border/80 bg-[linear-gradient(180deg,rgba(32,22,18,0.92),rgba(14,12,11,0.96))] px-5 py-8 shadow-[0_30px_80px_-40px_rgba(0,0,0,0.85)] md:px-10 md:py-10">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              'radial-gradient(ellipse 70% 50% at 50% 0%, rgba(201,100,66,0.18), transparent 60%)',
          }}
          aria-hidden
        />

        <h2 className="font-display relative z-10 mx-auto mb-10 max-w-2xl text-center text-2xl leading-tight tracking-[-0.02em] text-foreground md:mb-12 md:text-[1.85rem]">
          CoFound handles everything from idea to impact.
        </h2>

        {/* desktop journey */}
        <div className="relative z-10 hidden md:block">
          <div className="relative grid grid-cols-5 gap-3 lg:gap-4">
            {/* connector line behind icons */}
            <div
              className="pointer-events-none absolute left-[10%] right-[10%] top-[34px] h-px border-t border-dashed border-white/20"
              aria-hidden
            />

            {STEPS.map((step, index) => {
              const Icon = step.icon
              const isActive = active === index
              return (
                <button
                  key={step.id}
                  type="button"
                  onMouseEnter={() => setActive(index)}
                  onFocus={() => setActive(index)}
                  className="group relative flex flex-col items-center text-center outline-none"
                >
                  <span
                    className={cn(
                      'relative mb-4 flex size-[68px] items-center justify-center rounded-2xl border transition-all duration-500',
                      isActive ? 'scale-105 border-white/20' : 'border-white/10 opacity-80',
                    )}
                    style={{
                      background: `linear-gradient(160deg, ${step.accent}22, rgba(10,10,9,0.95))`,
                      boxShadow: isActive
                        ? `0 0 0 1px ${step.accent}55, 0 0 36px ${step.glow}`
                        : `0 0 18px ${step.glow}`,
                    }}
                  >
                    <Icon
                      className="size-6 transition-transform duration-500 group-hover:scale-110"
                      style={{ color: step.accent }}
                      aria-hidden
                    />
                    {isActive && (
                      <span
                        className="absolute -inset-1 -z-10 animate-pulse rounded-2xl opacity-60"
                        style={{ boxShadow: `0 0 28px ${step.glow}` }}
                        aria-hidden
                      />
                    )}
                  </span>
                  <span className="mb-2 text-sm font-semibold tracking-tight text-foreground">
                    {step.title}
                  </span>
                  <span
                    className={cn(
                      'max-w-[11.5rem] text-[12px] leading-relaxed text-muted-foreground transition-opacity duration-300',
                      isActive ? 'opacity-100' : 'opacity-70',
                    )}
                  >
                    {step.description}
                  </span>
                </button>
              )
            })}
          </div>

          {/* feedback loop path */}
          <div className="relative mx-auto mt-8 h-16 max-w-4xl" aria-hidden>
            <svg
              viewBox="0 0 800 64"
              className="h-full w-full overflow-visible"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M760 4 C760 36, 720 52, 400 52 C80 52, 40 36, 40 4"
                stroke="url(#loopStroke)"
                strokeWidth="1.5"
                strokeDasharray="6 7"
                className="founder-loop-path"
              />
              <path d="M40 4 L32 14 L48 14 Z" fill="#c96442" opacity="0.9" />
              <path d="M760 4 L752 14 L768 14 Z" fill="#c96442" opacity="0.55" />
              <defs>
                <linearGradient id="loopStroke" x1="40" y1="52" x2="760" y2="52" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#c96442" stopOpacity="0.85" />
                  <stop offset="0.5" stopColor="#e08a62" stopOpacity="0.7" />
                  <stop offset="1" stopColor="#c96442" stopOpacity="0.85" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute left-1/2 top-[34px] -translate-x-1/2 -translate-y-1/2">
              <span className="inline-flex items-center rounded-full border border-primary/40 bg-[#2a1a14]/95 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-primary shadow-[0_0_24px_rgba(201,100,66,0.25)]">
                Continuous feedback loop
              </span>
            </div>
          </div>
        </div>

        {/* mobile stack */}
        <div className="relative z-10 space-y-3 md:hidden">
          {STEPS.map((step, index) => {
            const Icon = step.icon
            const isActive = active === index
            return (
              <button
                key={step.id}
                type="button"
                onClick={() => setActive(index)}
                className={cn(
                  'flex w-full items-start gap-3 rounded-xl border px-3 py-3 text-left transition-all duration-300',
                  isActive ? 'border-primary/40 bg-card/50' : 'border-border/60 bg-card/20',
                )}
              >
                <span
                  className="mt-0.5 flex size-11 shrink-0 items-center justify-center rounded-xl border border-white/10"
                  style={{
                    background: `linear-gradient(160deg, ${step.accent}28, rgba(10,10,9,0.95))`,
                    boxShadow: `0 0 18px ${step.glow}`,
                  }}
                >
                  <Icon className="size-5" style={{ color: step.accent }} aria-hidden />
                </span>
                <span>
                  <span className="block text-sm font-semibold text-foreground">{step.title}</span>
                  <span className="mt-0.5 block text-xs leading-relaxed text-muted-foreground">
                    {step.description}
                  </span>
                </span>
              </button>
            )
          })}
          <div className="flex justify-center pt-2">
            <span className="inline-flex items-center rounded-full border border-primary/40 bg-[#2a1a14]/95 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-primary">
              Continuous feedback loop
            </span>
          </div>
        </div>
      </div>

      <style>{`
        .founder-loop-path {
          stroke-dashoffset: 0;
          animation: founder-loop-dash 18s linear infinite;
        }
        @keyframes founder-loop-dash {
          to { stroke-dashoffset: -260; }
        }
      `}</style>
    </section>
  )
}
