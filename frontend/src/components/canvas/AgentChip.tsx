import { cn } from '@/lib/utils'

interface AgentChipProps {
  label: string
  active?: boolean
}

export function AgentChip({ label, active = false }: AgentChipProps) {
  return (
    <span
      className={cn(
        'absolute -right-2 -top-2 flex size-5 items-center justify-center rounded-full border border-primary bg-card text-[10px] font-medium text-primary',
        active && 'agent-chip-active',
      )}
      aria-label={`Agent ${label} active`}
    >
      {label}
    </span>
  )
}
