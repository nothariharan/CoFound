import {
  Bot,
  ChevronDown,
  Download,
  GitBranch,
  History,
  LineChart,
  Plus,
} from 'lucide-react'
import { useWorkspaceStore } from '../../store/workspaceStore'

export function LeftRail() {
  const { workspace } = useWorkspaceStore()

  return (
    <aside className="flex h-full w-[220px] shrink-0 flex-col border-r border-[#e5e5e5] bg-white">
      <div className="border-b border-[#e5e5e5] p-4">
        <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
          Project
        </p>
        <button className="flex w-full items-center justify-between text-sm font-medium text-[#171717]">
          <span className="truncate">{workspace?.workspace_name ?? '—'}</span>
          <ChevronDown size={14} strokeWidth={1.5} className="shrink-0 text-[#737373]" />
        </button>
        <button className="mt-2 flex items-center gap-1.5 text-xs text-[#737373] hover:text-[#171717]">
          <Plus size={12} strokeWidth={1.5} />
          New Startup
        </button>
      </div>

      <div className="border-b border-[#e5e5e5] p-4">
        <div className="mb-2 flex items-center gap-2">
          <Bot size={14} strokeWidth={1.5} className="text-[#737373]" />
          <span className="text-xs font-medium text-[#171717]">Active Agents</span>
        </div>
        <p className="text-xs text-[#737373]">0 agents active</p>
      </div>

      <div className="border-b border-[#e5e5e5] p-4">
        <p className="mb-3 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
          Integrations
        </p>
        <div className="space-y-2">
          <IntegrationRow icon={GitBranch} label="GitHub" connected={false} />
          <IntegrationRow icon={LineChart} label="PostHog" connected={false} />
        </div>
      </div>

      <div className="border-b border-[#e5e5e5] p-4">
        <button className="flex items-center gap-2 text-xs text-[#737373] hover:text-[#171717]">
          <History size={14} strokeWidth={1.5} />
          Decision Journal
        </button>
      </div>

      <div className="p-4">
        <button
          disabled
          className="flex w-full items-center gap-2 rounded border border-[#e5e5e5] px-3 py-2 text-xs text-[#a3a3a3]"
        >
          <Download size={14} strokeWidth={1.5} />
          Export
        </button>
      </div>
    </aside>
  )
}

function IntegrationRow({
  icon: Icon,
  label,
  connected,
}: {
  icon: React.ComponentType<{ size?: number; strokeWidth?: number; className?: string }>
  label: string
  connected: boolean
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon size={14} strokeWidth={1.5} className="text-[#737373]" />
        <span className="text-xs text-[#171717]">{label}</span>
      </div>
      <span
        className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-[#16a34a]' : 'bg-[#e5e5e5]'}`}
      />
    </div>
  )
}
