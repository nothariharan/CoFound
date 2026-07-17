import { useEffect, useRef, type RefObject } from 'react'
import { gsap, useGSAP } from '@/lib/gsap'
import { createMotionMatchMedia, motionDuration } from '@/lib/gsap'
import { CursorLabel, CursorPointerIcon } from '@/components/cursor/CursorLabel'

// tip of the pointer svg sits upper-left — offset so it aims along travel
const POINTER_ANGLE_OFFSET = 135

type AgentSpec = {
  id: string
  label: string
  color: string
  // starting spot in % of the landing page
  x: number
  y: number
  // how often this agent picks a new wander target (ms) — staggered so they don't sync
  wanderEvery: [number, number]
  // how far they'll roam in one hop
  roam: number
}

const AGENTS: AgentSpec[] = [
  {
    id: 'orchestrator',
    label: 'Orchestrator',
    color: '#c96442',
    x: 12,
    y: 22,
    wanderEvery: [4200, 7200],
    roam: 18,
  },
  {
    id: 'researcher',
    label: 'Researcher',
    color: '#4a8eff',
    x: 10,
    y: 58,
    wanderEvery: [5100, 8600],
    roam: 16,
  },
  {
    id: 'builder',
    label: 'Builder',
    color: '#6366f1',
    x: 82,
    y: 28,
    wanderEvery: [4800, 7800],
    roam: 17,
  },
  {
    id: 'growth',
    label: 'Growth',
    color: '#22c55e',
    x: 78,
    y: 62,
    wanderEvery: [5600, 9200],
    roam: 15,
  },
  {
    id: 'validator',
    label: 'Validator',
    color: '#5fb87a',
    x: 48,
    y: 78,
    wanderEvery: [6000, 9800],
    roam: 14,
  },
]

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function rand(min: number, max: number) {
  return min + Math.random() * (max - min)
}

function AgentCursor({
  label,
  color,
  agentId,
}: {
  label: string
  color: string
  agentId: string
}) {
  return (
    <div
      className="agent-cursor absolute left-0 top-0 will-change-transform"
      data-agent={agentId}
      style={{ transform: 'translate3d(0,0,0)' }}
    >
      <div className="agent-cursor-inner relative origin-top-left">
        <CursorPointerIcon color={color} size={24} />
        <div className="absolute left-5 top-5">
          <CursorLabel label={label} color={color} />
        </div>
      </div>
    </div>
  )
}

type AgentCursorsProps = {
  /** optional work target — agents sometimes drift toward the idea input */
  targetRef?: RefObject<HTMLElement | null>
}

export function AgentCursors({ targetRef }: AgentCursorsProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mouseRef = useRef({ x: -9999, y: -9999, active: false })

  // track real mouse so agents can dodge when you get close
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY, active: true }
    }
    const onLeave = () => {
      mouseRef.current.active = false
    }
    window.addEventListener('mousemove', onMove, { passive: true })
    window.addEventListener('mouseleave', onLeave)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseleave', onLeave)
    }
  }, [])

  useGSAP(
    () => {
      const mm = createMotionMatchMedia()
      mm.add(({ reduceMotion }) => {
        const layer = containerRef.current
        if (!layer) return

        const cursors = gsap.utils.toArray<HTMLElement>('.agent-cursor', layer)
        const cleanups: Array<() => void> = []

        // fade in staggered — not all popping at once
        gsap.from(cursors, {
          autoAlpha: 0,
          scale: reduceMotion ? 1 : 0.88,
          duration: motionDuration(reduceMotion, 0.65, 0.01),
          stagger: 0.18,
          ease: 'back.out(1.3)',
          delay: 0.55,
        })

        if (reduceMotion) {
          // park them at start spots and bail
          cursors.forEach((el, i) => {
            const agent = AGENTS[i]
            if (!agent) return
            const w = layer.clientWidth
            const h = layer.clientHeight
            gsap.set(el, { x: (agent.x / 100) * w, y: (agent.y / 100) * h })
          })
          return
        }

        cursors.forEach((el, i) => {
          const agent = AGENTS[i]
          if (!agent) return
          const inner = el.querySelector<HTMLElement>('.agent-cursor-inner')
          if (!inner) return

          let x = (agent.x / 100) * layer.clientWidth
          let y = (agent.y / 100) * layer.clientHeight
          gsap.set(el, { x, y })
          gsap.set(inner, { rotation: POINTER_ANGLE_OFFSET + rand(-12, 12) })

          let fleeTween: gsap.core.Tween | null = null
          let wanderTween: gsap.core.Tween | null = null
          let nextWanderAt = performance.now() + rand(...agent.wanderEvery)
          let busyUntil = 0

          const bounds = () => {
            const w = layer.clientWidth
            const h = layer.clientHeight
            // keep labels on-screen with a soft margin
            return {
              minX: w * 0.04,
              maxX: w * 0.88,
              minY: h * 0.1,
              maxY: h * 0.86,
              w,
              h,
            }
          }

          const moveTo = (nx: number, ny: number, duration: number, ease = 'power2.inOut') => {
            const b = bounds()
            const tx = clamp(nx, b.minX, b.maxX)
            const ty = clamp(ny, b.minY, b.maxY)
            const dx = tx - x
            const dy = ty - y
            const angle = (Math.atan2(dy, dx) * 180) / Math.PI + POINTER_ANGLE_OFFSET

            gsap.to(inner, {
              rotation: angle,
              duration: Math.min(0.55, duration * 0.35),
              ease: 'sine.out',
              overwrite: 'auto',
            })

            wanderTween?.kill()
            wanderTween = gsap.to(el, {
              x: tx,
              y: ty,
              duration,
              ease,
              overwrite: 'auto',
              onUpdate: () => {
                x = Number(gsap.getProperty(el, 'x'))
                y = Number(gsap.getProperty(el, 'y'))
              },
              onComplete: () => {
                x = tx
                y = ty
              },
            })
          }

          const pickWander = () => {
            if (performance.now() < busyUntil) return
            const b = bounds()
            // ~1 in 4 hops drift toward the idea input so it feels like work
            const targetEl = targetRef?.current
            let nx = x + rand(-agent.roam, agent.roam) * (b.w / 100)
            let ny = y + rand(-agent.roam, agent.roam) * (b.h / 100)

            if (targetEl && Math.random() < 0.28) {
              const rect = targetEl.getBoundingClientRect()
              const layerRect = layer.getBoundingClientRect()
              nx = rect.left - layerRect.left + rand(20, Math.max(40, rect.width - 40))
              ny = rect.top - layerRect.top + rand(-36, 28)
            }

            moveTo(nx, ny, rand(1.6, 2.8))
            nextWanderAt = performance.now() + rand(...agent.wanderEvery)
          }

          // kick off first roam at staggered times so nothing syncs
          const startDelay = window.setTimeout(
            () => {
              pickWander()
            },
            700 + i * 420 + rand(0, 400),
          )

          const tick = () => {
            const now = performance.now()
            const mouse = mouseRef.current
            const layerRect = layer.getBoundingClientRect()
            const cx = layerRect.left + x
            const cy = layerRect.top + y

            // dodge the real cursor when it gets close
            if (mouse.active) {
              const dx = cx - mouse.x
              const dy = cy - mouse.y
              const dist = Math.hypot(dx, dy)
              const fleeRadius = 120
              if (dist < fleeRadius && dist > 0.1) {
                const push = (fleeRadius - dist) / fleeRadius
                const nx = x + (dx / dist) * (40 + push * 90) + rand(-10, 10)
                const ny = y + (dy / dist) * (40 + push * 90) + rand(-10, 10)
                busyUntil = now + 900
                fleeTween?.kill()
                fleeTween = gsap.to(el, {
                  x: clamp(nx, bounds().minX, bounds().maxX),
                  y: clamp(ny, bounds().minY, bounds().maxY),
                  duration: 0.45 + push * 0.25,
                  ease: 'power3.out',
                  overwrite: 'auto',
                  onUpdate: () => {
                    x = Number(gsap.getProperty(el, 'x'))
                    y = Number(gsap.getProperty(el, 'y'))
                  },
                })
                const angle = (Math.atan2(ny - y, nx - x) * 180) / Math.PI + POINTER_ANGLE_OFFSET
                gsap.to(inner, { rotation: angle, duration: 0.25, overwrite: 'auto' })
                nextWanderAt = now + rand(900, 1600)
              }
            }

            if (now >= nextWanderAt) pickWander()
          }

          gsap.ticker.add(tick)
          cleanups.push(() => {
            window.clearTimeout(startDelay)
            gsap.ticker.remove(tick)
            fleeTween?.kill()
            wanderTween?.kill()
          })

          // tiny idle bob so they feel alive between hops
          gsap.to(inner, {
            scale: 1.04,
            duration: 1.7 + i * 0.22,
            repeat: -1,
            yoyo: true,
            ease: 'sine.inOut',
            delay: i * 0.35,
          })
        })

        return () => {
          cleanups.forEach((fn) => fn())
        }
      }, containerRef.current)

      return () => mm.revert()
    },
    { scope: containerRef, dependencies: [targetRef] },
  )

  return (
    <div
      ref={containerRef}
      className="agent-cursors-layer pointer-events-none absolute inset-0 z-[60] overflow-hidden"
      aria-hidden
    >
      {AGENTS.map((agent) => (
        <AgentCursor key={agent.id} agentId={agent.id} label={agent.label} color={agent.color} />
      ))}
    </div>
  )
}
