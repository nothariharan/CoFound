import { useRef } from 'react'
import { gsap, useGSAP } from '@/lib/gsap'
import { createMotionMatchMedia, motionDuration, motionStagger } from '@/lib/gsap'

export function useIntakeAnimation() {
  const containerRef = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const mm = createMotionMatchMedia()
      mm.add(({ reduceMotion }) => {
        gsap.from('.intake-animate', {
          autoAlpha: 0,
          y: reduceMotion ? 0 : 16,
          duration: motionDuration(reduceMotion, 0.4),
          stagger: motionStagger(reduceMotion, 0.08),
          ease: 'power2.out',
        })
      }, containerRef.current)
      return () => mm.revert()
    },
    { scope: containerRef },
  )

  return containerRef
}

export function useShellEntrance() {
  const shellRef = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const mm = createMotionMatchMedia()
      mm.add(({ reduceMotion }) => {
        gsap.from('.shell-panel', {
          autoAlpha: 0,
          x: reduceMotion ? 0 : -8,
          duration: motionDuration(reduceMotion, 0.3),
          stagger: motionStagger(reduceMotion, 0.05),
          ease: 'power2.out',
        })
      }, shellRef.current)
      return () => mm.revert()
    },
    { scope: shellRef },
  )

  return shellRef
}

export function useCanvasUnlockAnimation(nodeIds: string[]) {
  const canvasRef = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      if (!nodeIds.length) return
      const mm = createMotionMatchMedia()
      mm.add(({ reduceMotion }) => {
        gsap.from(
          nodeIds.map((id) => `[data-node-id="${id}"]`),
          {
            autoAlpha: 0,
            scale: reduceMotion ? 1 : 0.92,
            y: reduceMotion ? 0 : 12,
            duration: motionDuration(reduceMotion, 0.35),
            stagger: motionStagger(reduceMotion, 0.06),
            ease: 'back.out(1.4)',
          },
        )
      }, canvasRef.current)
      return () => mm.revert()
    },
    { scope: canvasRef, dependencies: [nodeIds.join(',')] },
  )

  return canvasRef
}
