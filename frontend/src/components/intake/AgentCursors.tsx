import { useRef, type RefObject } from 'react'
import { gsap, useGSAP } from '@/lib/gsap'
import { createMotionMatchMedia, motionDuration } from '@/lib/gsap'
import { CursorLabel, CursorPointerIcon } from '@/components/cursor/CursorLabel'

/** Cursor icon tip points upper-left at 0deg; offset so tip aims at target angle. */
const POINTER_ANGLE_OFFSET = 135

const AGENTS = [
  {
    id: 'orchestrator',
    label: 'Orchestrator',
    color: '#c96442',
    top: '18%',
    left: '8%',
    driftX: 28,
    driftY: 22,
  },
  {
    id: 'researcher',
    label: 'Researcher',
    color: '#4a8eff',
    top: '42%',
    left: '5%',
    driftX: 32,
    driftY: 10,
  },
  {
    id: 'validator',
    label: 'Validator',
    color: '#5fb87a',
    top: '68%',
    left: '12%',
    driftX: 34,
    driftY: -14,
  },
  {
    id: 'builder',
    label: 'Builder',
    color: '#6366f1',
    top: '22%',
    right: '8%',
    driftX: -30,
    driftY: 20,
  },
  {
    id: 'growth',
    label: 'Growth',
    color: '#22c55e',
    top: '48%',
    right: '6%',
    driftX: -34,
    driftY: 8,
  },
  {
    id: 'market',
    label: 'Market Analyst',
    color: '#d9a441',
    top: '72%',
    right: '14%',
    driftX: -32,
    driftY: -12,
  },
] as const

function computeAimRotation(
  cursorEl: HTMLElement,
  targetEl: HTMLElement,
): { rotation: number; driftX: number; driftY: number } {
  const targetRect = targetEl.getBoundingClientRect()
  const cursorRect = cursorEl.getBoundingClientRect()

  const targetX = targetRect.left + targetRect.width / 2
  const targetY = targetRect.top + targetRect.height / 2
  const cursorX = cursorRect.left + cursorRect.width / 2
  const cursorY = cursorRect.top + cursorRect.height / 2

  const dx = targetX - cursorX
  const dy = targetY - cursorY
  const angleRad = Math.atan2(dy, dx)
  const rotation = (angleRad * 180) / Math.PI + POINTER_ANGLE_OFFSET

  const dist = Math.min(36, Math.hypot(dx, dy) * 0.07)
  return {
    rotation,
    driftX: Math.cos(angleRad) * dist,
    driftY: Math.sin(angleRad) * dist,
  }
}

function AgentCursor({
  label,
  color,
  style,
}: {
  label: string
  color: string
  style: React.CSSProperties
}) {
  return (
    <div className="agent-cursor absolute" style={style}>
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
  targetRef?: RefObject<HTMLElement | null>
}

export function AgentCursors({ targetRef }: AgentCursorsProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const mm = createMotionMatchMedia()
      mm.add(({ reduceMotion }) => {
        const runAnimations = () => {
          const targetEl = targetRef?.current
          const cursors = gsap.utils.toArray<HTMLElement>('.agent-cursor', containerRef.current)

          gsap.from(cursors, {
            autoAlpha: 0,
            scale: reduceMotion ? 1 : 0.85,
            duration: motionDuration(reduceMotion, 0.7, 0.01),
            stagger: 0.12,
            ease: 'back.out(1.4)',
            delay: 0.6,
          })

          if (reduceMotion) return

          cursors.forEach((cursorEl, i) => {
            const inner = cursorEl.querySelector<HTMLElement>('.agent-cursor-inner')
            if (!inner) return

            const agent = AGENTS[i]
            if (!agent) return

            let rotation = POINTER_ANGLE_OFFSET
            let driftX: number = agent.driftX
            let driftY: number = agent.driftY

            if (targetEl) {
              const aimed = computeAimRotation(cursorEl, targetEl)
              rotation = aimed.rotation
              driftX = aimed.driftX
              driftY = aimed.driftY
            }

            gsap.set(inner, { rotation, x: 0, y: 0, scale: 1 })

            gsap.to(inner, {
              x: driftX,
              y: driftY,
              duration: 2.2 + i * 0.25,
              repeat: -1,
              yoyo: true,
              ease: 'sine.inOut',
              delay: i * 0.14,
            })

            gsap.to(inner, {
              rotation: rotation + (i % 2 === 0 ? 7 : -7),
              duration: 1.8 + i * 0.15,
              repeat: -1,
              yoyo: true,
              ease: 'sine.inOut',
              delay: i * 0.2,
            })

            gsap.to(inner, {
              scale: 1.07,
              duration: 1.5 + i * 0.1,
              repeat: -1,
              yoyo: true,
              ease: 'sine.inOut',
              delay: i * 0.26,
            })
          })
        }

        gsap.delayedCall(0.15, runAnimations)
      }, containerRef.current)
      return () => mm.revert()
    },
    { scope: containerRef },
  )

  return (
    <div
      ref={containerRef}
      className="agent-cursors-layer pointer-events-none absolute inset-0 z-[60] overflow-hidden"
      aria-hidden
    >
      {AGENTS.map((agent) => (
        <AgentCursor
          key={agent.id}
          label={agent.label}
          color={agent.color}
          style={{
            top: agent.top,
            left: 'left' in agent ? agent.left : undefined,
            right: 'right' in agent ? agent.right : undefined,
          }}
        />
      ))}
    </div>
  )
}
