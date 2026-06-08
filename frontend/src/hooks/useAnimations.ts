import { useRef } from 'react'
import { gsap, useGSAP } from '@/lib/gsap'
import { createMotionMatchMedia, motionDuration, motionStagger } from '@/lib/gsap'

export function useIntakeAnimation() {
  const containerRef = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const mm = createMotionMatchMedia()
      mm.add(({ reduceMotion }) => {
        const ease = 'power3.out'
        const dur = motionDuration(reduceMotion, 0.85, 0.01)

        const tl = gsap.timeline({ defaults: { ease } })

        tl.from('.intake-nav', {
          autoAlpha: 0,
          y: reduceMotion ? 0 : -12,
          duration: dur,
        })
          .from(
            '.intake-logo-watermark',
            {
              autoAlpha: 0,
              scale: reduceMotion ? 1 : 0.92,
              duration: motionDuration(reduceMotion, 1.2, 0.01),
            },
            '-=0.4',
          )
          .from(
            '.intake-hero-badge',
            { autoAlpha: 0, y: reduceMotion ? 0 : 20, duration: dur },
            '-=0.85',
          )
          .from(
            '.intake-hero-title',
            { autoAlpha: 0, y: reduceMotion ? 0 : 24, duration: dur },
            '-=0.65',
          )
          .from(
            '.intake-hero-sub',
            { autoAlpha: 0, y: reduceMotion ? 0 : 18, duration: dur },
            '-=0.7',
          )
          .from(
            '.intake-input-shell',
            {
              autoAlpha: 0,
              y: reduceMotion ? 0 : 20,
              scale: reduceMotion ? 1 : 0.98,
              duration: dur,
            },
            '-=0.65',
          )
          .from(
            '.intake-agent-gallery',
            {
              autoAlpha: 0,
              y: reduceMotion ? 0 : 24,
              duration: motionDuration(reduceMotion, 0.8, 0.01),
            },
            '-=0.5',
          )

        if (!reduceMotion) {
          gsap.to('.intake-logo-watermark', {
            scale: 1.03,
            duration: 4,
            repeat: -1,
            yoyo: true,
            ease: 'sine.inOut',
          })
        }
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
