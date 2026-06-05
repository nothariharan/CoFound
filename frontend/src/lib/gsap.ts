import { gsap } from 'gsap'
import { useGSAP } from '@gsap/react'

gsap.registerPlugin(useGSAP)

export { gsap, useGSAP }

export type MotionContext = {
  reduceMotion: boolean
}

export function createMotionMatchMedia() {
  const mm = gsap.matchMedia()

  return {
    add(
      callback: (context: MotionContext) => void | (() => void),
      scope?: Element | null,
    ) {
      return mm.add(
        { reduceMotion: '(prefers-reduced-motion: reduce)' },
        (ctx) => {
          const reduceMotion = Boolean(ctx.conditions?.reduceMotion)
          return callback({ reduceMotion })
        },
        scope ?? undefined,
      )
    },
    revert() {
      mm.revert()
    },
  }
}

export function motionDuration(reduceMotion: boolean, normal = 0.25, reduced = 0) {
  return reduceMotion ? reduced : normal
}

export function motionStagger(reduceMotion: boolean, normal = 0.04, reduced = 0) {
  return reduceMotion ? reduced : normal
}
