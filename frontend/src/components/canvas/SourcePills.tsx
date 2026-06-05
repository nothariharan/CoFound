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
          className="rounded border border-border bg-background px-2 py-0.5 text-[10px] text-muted-foreground"
        >
          {pill.label}
          {pill.count > 0 && ` · ${pill.count}`}
        </span>
      ))}
    </div>
  )
}
