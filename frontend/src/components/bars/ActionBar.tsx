import { Check } from 'lucide-react'
import { useWorkspaceStore } from '../../store/workspaceStore'

export function ActionBar() {
  const { todayPriority } = useWorkspaceStore()

  return (
    <footer className="flex h-14 shrink-0 items-center justify-between border-t border-[#e5e5e5] bg-white px-4">
      <div className="flex items-center gap-6">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wide text-[#737373]">
            Today&apos;s Priority
          </p>
          <p className="text-sm font-medium text-[#171717]">{todayPriority.action}</p>
        </div>
        <div className="hidden sm:block">
          <p className="text-[10px] font-medium uppercase tracking-wide text-[#737373]">
            Why
          </p>
          <p className="text-sm text-[#737373]">{todayPriority.reason}</p>
        </div>
        {todayPriority.estimatedTime && (
          <p className="hidden text-xs text-[#a3a3a3] md:block">
            ~{todayPriority.estimatedTime}
          </p>
        )}
      </div>
      <button className="inline-flex items-center gap-2 rounded border border-[#e5e5e5] px-4 py-2 text-sm text-[#171717] hover:border-[#d4d4d4]">
        <Check size={14} strokeWidth={1.5} />
        Done
      </button>
    </footer>
  )
}
