import { getRingColor } from '../../utils/nodeColors'

interface ConfidenceRingProps {
  confidence: number
  status: 'validated' | 'needs_work' | 'blocking' | 'locked'
  size?: number
}

export function ConfidenceRing({ confidence, status, size = 44 }: ConfidenceRingProps) {
  const stroke = 3
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (confidence / 100) * circumference
  const color = getRingColor(confidence, status)

  return (
    <svg width={size} height={size} className="shrink-0">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#e5e5e5"
        strokeWidth={stroke}
      />
      <circle
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
        fill="#171717"
        fontSize="11"
        fontWeight="500"
      >
        {Math.round(confidence)}
      </text>
    </svg>
  )
}
