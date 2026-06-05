import { useEffect, useRef } from 'react'
import { gsap } from '@/lib/gsap'
import { getRingColor } from '@/utils/nodeColors'
import { createMotionMatchMedia, motionDuration } from '@/lib/gsap'

interface ConfidenceRingProps {
  confidence: number
  status: 'validated' | 'needs_work' | 'blocking' | 'locked'
  size?: number
}

export function ConfidenceRing({ confidence, status, size = 44 }: ConfidenceRingProps) {
  const stroke = 3
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const color = getRingColor(confidence, status)
  const ringRef = useRef<SVGCircleElement>(null)
  const prevConfidence = useRef(confidence)

  useEffect(() => {
    if (!ringRef.current || prevConfidence.current === confidence) return

    const mm = createMotionMatchMedia()
    mm.add(({ reduceMotion }) => {
      const offset = circumference - (confidence / 100) * circumference
      gsap.to(ringRef.current, {
        strokeDashoffset: offset,
        duration: motionDuration(reduceMotion, 0.6),
        ease: 'power2.out',
      })
    })

    prevConfidence.current = confidence
    return () => mm.revert()
  }, [confidence, circumference])

  const offset = circumference - (confidence / 100) * circumference

  return (
    <svg width={size} height={size} className="shrink-0" aria-label={`Confidence ${Math.round(confidence)}%`}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--border)"
        strokeWidth={stroke}
      />
      <circle
        ref={ringRef}
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={stroke}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text
        x="50%"
        y="50%"
        dominantBaseline="central"
        textAnchor="middle"
        fill="var(--foreground)"
        fontSize="11"
        fontWeight="500"
        className="tabular-nums"
      >
        {Math.round(confidence)}
      </text>
    </svg>
  )
}
