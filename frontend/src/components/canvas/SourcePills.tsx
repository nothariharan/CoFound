import { statusLabels } from '../../utils/nodeColors'

interface SourcePillsProps {
  pills: { label: string; count: number }[]
}

export function SourcePills({ pills }: SourcePillsProps) {
  if (!pills.length) return null
  return (
    <div className="flex flex-wrap gap-1.5">
      {pills.map((pill) => (
        <span
          key={pill.label}
          className="rounded border border-[#e5e5e5] bg-[#fafafa] px-2 py-0.5 text-[10px] text-[#737373]"
        >
          {pill.label}
          {pill.count > 0 && ` · ${pill.count}`}
        </span>
      ))}
    </div>
  )
}

export { statusLabels }
