const ORBIT_NODES = [
  { id: 'audience', label: 'Audience', color: '#a78bfa', angle: -135 },
  { id: 'market', label: 'Market Intelligence', color: '#5fb87a', angle: -90 },
  { id: 'competitors', label: 'Competitors', color: '#5fb87a', angle: -45 },
  { id: 'product', label: 'Product Vision', color: '#c96442', angle: 15 },
  { id: 'growth', label: 'Growth', color: '#c96442', angle: 55 },
  { id: 'observe', label: 'Observe', color: '#4a8eff', angle: 90 },
  { id: 'build', label: 'Build', color: '#4a8eff', angle: 135 },
  { id: 'revenue', label: 'Revenue Model', color: '#5fb87a', angle: 180 },
] as const

function CoFoundMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden>
      <circle cx="16" cy="8" r="2" fill="currentColor" opacity="0.9" />
      <circle cx="24" cy="12" r="2" fill="currentColor" opacity="0.7" />
      <circle cx="26" cy="20" r="2" fill="currentColor" opacity="0.5" />
      <circle cx="20" cy="26" r="2" fill="currentColor" opacity="0.7" />
      <circle cx="12" cy="26" r="2" fill="currentColor" opacity="0.5" />
      <circle cx="6" cy="20" r="2" fill="currentColor" opacity="0.7" />
      <circle cx="8" cy="12" r="2" fill="currentColor" opacity="0.9" />
      <circle cx="16" cy="16" r="2.5" fill="currentColor" />
    </svg>
  )
}

function NodeIcon({ id }: { id: string }) {
  const stroke = 'currentColor'
  const common = { stroke, strokeWidth: 1.5, fill: 'none', strokeLinecap: 'round' as const }

  switch (id) {
    case 'audience':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <circle cx="8" cy="5" r="2.5" {...common} />
          <path d="M3 14c0-2.8 2.2-5 5-5s5 2.2 5 5" {...common} />
        </svg>
      )
    case 'market':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <path d="M2 12 L6 8 L9 10 L14 4" {...common} />
          <path d="M11 4 h3 v3" {...common} />
        </svg>
      )
    case 'competitors':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <circle cx="8" cy="8" r="5" {...common} />
          <circle cx="8" cy="8" r="2" {...common} />
        </svg>
      )
    case 'product':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <path d="M3 5 L8 2 L13 5 L13 11 L8 14 L3 11 Z" {...common} />
        </svg>
      )
    case 'growth':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <path d="M2 12 L6 8 L9 10 L14 4" {...common} />
        </svg>
      )
    case 'observe':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <circle cx="8" cy="8" r="2" {...common} />
          <path d="M2 8c1.5-3 4-4.5 6-4.5s4.5 1.5 6 4.5c-1.5 3-4 4.5-6 4.5S3.5 11 2 8Z" {...common} />
        </svg>
      )
    case 'build':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <path d="M5 4 L11 4 L11 12 L5 12 Z" {...common} />
          <path d="M7 7 L9 7 M7 9.5 L9 9.5" {...common} />
        </svg>
      )
    case 'revenue':
      return (
        <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
          <path d="M3 8h10 M8 3v10" {...common} />
          <circle cx="8" cy="8" r="5" {...common} />
        </svg>
      )
    default:
      return null
  }
}

export function OrbitalDiagram() {
  const radius = 168
  const center = { x: 280, y: 200 }

  return (
    <div className="orbit-stage intake-orbit relative mx-auto w-full max-w-[560px]">
      <svg
        className="orbit-ring intake-orbit-ring pointer-events-none absolute inset-0 mx-auto h-full w-full"
        viewBox="0 0 560 400"
        aria-hidden
      >
        <ellipse
          cx={center.x}
          cy={center.y}
          rx={radius + 20}
          ry={radius * 0.55}
          fill="none"
          stroke="#222220"
          strokeWidth="1"
        />
        <ellipse
          cx={center.x}
          cy={center.y}
          rx={radius - 30}
          ry={radius * 0.4}
          fill="none"
          stroke="#222220"
          strokeWidth="1"
          opacity="0.6"
        />
        {ORBIT_NODES.map((node) => {
          const rad = (node.angle * Math.PI) / 180
          const x = center.x + Math.cos(rad) * radius
          const y = center.y + Math.sin(rad) * (radius * 0.55)
          return (
            <line
              key={`line-${node.id}`}
              className="orbit-spoke"
              x1={center.x}
              y1={center.y}
              x2={x}
              y2={y}
              stroke="#222220"
              strokeWidth="1"
            />
          )
        })}
      </svg>

      <div
        className="orbit-core intake-orbit-core absolute left-1/2 top-1/2 z-10 flex size-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-card"
        aria-hidden
      >
        <div className="flex size-12 items-center justify-center rounded-full border border-border bg-surface-elevated text-foreground">
          <CoFoundMark className="size-7" />
        </div>
      </div>

      {ORBIT_NODES.map((node) => {
        const rad = (node.angle * Math.PI) / 180
        const x = Math.cos(rad) * radius
        const y = Math.sin(rad) * (radius * 0.55)

        return (
          <div
            key={node.id}
            className="orbit-node intake-orbit-node absolute left-1/2 top-1/2 z-20"
            style={{
              transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
            }}
          >
            <div className="orbit-node-inner">
              <div
                className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 whitespace-nowrap"
                style={{ borderColor: `${node.color}40`, color: node.color }}
              >
                <NodeIcon id={node.id} />
                <span className="text-xs font-medium text-foreground">{node.label}</span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function CoFoundLogo({
  className,
  markClassName,
}: {
  className?: string
  markClassName?: string
}) {
  return (
    <div className={className}>
      <CoFoundMark className={markClassName ?? 'size-6 text-foreground'} />
    </div>
  )
}
