interface AgentChipProps {
  label: string
}

export function AgentChip({ label }: AgentChipProps) {
  return (
    <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full border border-[#2563eb] bg-white text-[10px] font-medium text-[#2563eb]">
      {label}
    </span>
  )
}
