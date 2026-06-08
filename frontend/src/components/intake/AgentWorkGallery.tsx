import { useState } from 'react'
import { motion } from 'motion/react'
import {
  Bot,
  Code2,
  LineChart,
  Network,
  Search,
  Target,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/utils'

type AgentWorkCard = {
  id: string
  label: string
  headline: string
  description: string
  color: string
  icon: LucideIcon
  image: string
}

const AGENT_CARDS: AgentWorkCard[] = [
  {
    id: 'orchestrator',
    label: 'Orchestrator',
    headline: 'Coordinates every agent',
    description:
      'Routes tasks, resolves conflicts, and keeps your entire startup graph moving in sync.',
    color: '#c96442',
    icon: Network,
    image:
      'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=600&fit=crop&q=80',
  },
  {
    id: 'researcher',
    label: 'Researcher',
    headline: 'Maps markets and trends',
    description:
      'Scans industry data, customer signals, and emerging opportunities around your idea.',
    color: '#4a8eff',
    icon: Search,
    image:
      'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=600&fit=crop&q=80',
  },
  {
    id: 'validator',
    label: 'Validator',
    headline: 'Tests assumptions fast',
    description:
      'Pressure-tests demand, pricing, and positioning before you commit months of build time.',
    color: '#5fb87a',
    icon: Target,
    image:
      'https://images.unsplash.com/photo-1553877522-43269d4ea984?w=800&h=600&fit=crop&q=80',
  },
  {
    id: 'builder',
    label: 'Builder',
    headline: 'Ships product direction',
    description:
      'Turns validated insights into concrete product specs, tech choices, and launch plans.',
    color: '#6366f1',
    icon: Code2,
    image:
      'https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=600&fit=crop&q=80',
  },
  {
    id: 'growth',
    label: 'Growth',
    headline: 'Scales what works',
    description:
      'Identifies channels, loops, and experiments to compound traction after launch.',
    color: '#22c55e',
    icon: LineChart,
    image:
      'https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=800&h=600&fit=crop&q=80',
  },
  {
    id: 'market',
    label: 'Market Analyst',
    headline: 'Tracks competitors',
    description:
      'Monitors rival moves, whitespace, and positioning so you stay ahead of the landscape.',
    color: '#d9a441',
    icon: Bot,
    image:
      'https://images.unsplash.com/photo-1542744094-3a31f272c490?w=800&h=600&fit=crop&q=80',
  },
]

const CARD_SHADOW = `
  rgba(0, 0, 0, 0.02) 0.8px 0px 0.8px 0px,
  rgba(0, 0, 0, 0.05) 2.4px 0px 2.4px 0px,
  rgba(0, 0, 0, 0.1) 6px 0px 6px 0px,
  rgba(0, 0, 0, 0.28) 18px 0px 18px 0px
`

function AgentWorkCardFace({
  card,
  isHovered,
}: {
  card: AgentWorkCard
  isHovered: boolean
}) {
  const Icon = card.icon

  return (
    <div className="agent-work-card-face flex h-full flex-col overflow-hidden rounded-xl border border-border bg-card/85 backdrop-blur-sm">
      <div className="flex flex-col gap-2 p-4 pb-3">
        <div
          className="flex size-9 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${card.color}22`, color: card.color }}
        >
          <Icon className="size-4" aria-hidden />
        </div>
        <div>
          <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            {card.label}
          </p>
          <h3 className="text-sm font-semibold leading-snug text-foreground">{card.headline}</h3>
        </div>
        <p
          className={cn(
            'text-xs leading-relaxed text-muted-foreground transition-all duration-300',
            isHovered ? 'max-h-24 opacity-100' : 'max-h-0 overflow-hidden opacity-0',
          )}
        >
          {card.description}
        </p>
      </div>
      <div className="relative mt-auto aspect-video overflow-hidden">
        <img
          src={card.image}
          alt={card.headline}
          className={cn(
            'h-full w-full object-cover object-left-top transition-transform duration-500',
            isHovered ? 'scale-110' : 'scale-100',
          )}
          loading="lazy"
          decoding="async"
        />
        <div
          className={cn(
            'absolute inset-0 bg-gradient-to-t from-card via-card/20 to-transparent transition-opacity duration-300',
            isHovered ? 'opacity-40' : 'opacity-70',
          )}
        />
      </div>
    </div>
  )
}

type AgentWorkGalleryProps = {
  className?: string
  maxHeight?: number
  spacing?: string
}

export function AgentWorkGallery({
  className = '',
  maxHeight = 48,
  spacing = '-space-x-10 md:-space-x-14 lg:-space-x-16 xl:-space-x-20',
}: AgentWorkGalleryProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const cards = AGENT_CARDS

  return (
    <section
      aria-label="What your agents do"
      className={cn(
        'intake-agent-gallery relative z-30 w-[100vw] max-w-[1400px] left-1/2 -translate-x-1/2 px-4 md:px-8',
        className,
      )}
    >
      <p className="mb-4 text-center text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
        What your agents do
      </p>

      <div className="hidden md:block relative overflow-visible h-[360px] -mt-2">
        <div className={cn('flex items-center justify-center pt-4', spacing)}>
          {cards.map((card, index) => {
            const total = cards.length
            const middle = (total - 1) / 2
            const distanceFromMiddle = Math.abs(index - middle)
            const staggerOffset = maxHeight - distanceFromMiddle * 12

            const isHovered = hoveredIndex === index
            const isOtherHovered = hoveredIndex !== null && hoveredIndex !== index
            const yOffset = isHovered ? -100 : isOtherHovered ? 0 : -staggerOffset

            return (
              <motion.div
                key={card.id}
                className="group agent-work-card pointer-events-auto shrink-0"
                style={{ zIndex: isHovered ? 50 : 10 }}
                initial={{
                  transform: 'perspective(5000px) rotateY(-35deg) translateY(160px)',
                  opacity: 0,
                }}
                animate={{
                  transform: `perspective(5000px) rotateY(-35deg) translateY(${yOffset}px)`,
                  opacity: 1,
                }}
                transition={{
                  duration: 0.22,
                  delay: index * 0.05,
                  ease: [0.25, 0.1, 0.25, 1],
                }}
                onHoverStart={() => setHoveredIndex(index)}
                onHoverEnd={() => setHoveredIndex(null)}
              >
                <div
                  className="agent-work-card-shell relative w-48 lg:w-56 xl:w-64 transition-transform duration-300 group-hover:scale-[1.02]"
                  style={{ boxShadow: CARD_SHADOW }}
                >
                  <AgentWorkCardFace card={card} isHovered={isHovered} />
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      <div className="block md:hidden relative pb-4">
        <div className="group flex overflow-hidden p-2 [--duration:38s] [--gap:1rem] [gap:var(--gap)] flex-row">
          {Array.from({ length: 2 }).map((_, repeatIndex) => (
            <div
              key={repeatIndex}
              className="flex shrink-0 justify-around [gap:var(--gap)] animate-marquee flex-row group-hover:[animation-play-state:paused]"
            >
              {cards.map((card) => (
                <div key={`${repeatIndex}-${card.id}`} className="agent-work-card shrink-0">
                  <div
                    className="agent-work-card-shell w-64 overflow-hidden rounded-xl"
                    style={{ boxShadow: CARD_SHADOW }}
                  >
                    <AgentWorkCardFace card={card} isHovered={false} />
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
