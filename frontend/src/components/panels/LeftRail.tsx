import {
  Bot,
  ChevronDown,
  Download,
  GitBranch,
  History,
  LineChart,
  Mail,
  MessageSquare,
  Plus,
  Search,
  Settings,
} from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

export function LeftRail() {
  const { workspace, agents, integrations, projects, setJournalOpen, setExportOpen } = useWorkspaceStore()

  return (
    <aside className="shell-panel flex h-full w-[220px] shrink-0 flex-col border-r border-border bg-card">
      <div className="border-b border-border p-4">
        <p className="text-sm font-semibold text-foreground">CoFound</p>
      </div>

      <div className="border-b border-border p-4">
        <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Project</p>
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-md py-1 text-sm font-medium text-foreground hover:text-primary"
          aria-label="Switch project"
        >
          <span className="truncate">{workspace?.workspace_name ?? 'Restaurant Copilot'}</span>
          <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" />
        </button>
        <Button variant="ghost" size="sm" className="mt-2 h-8 gap-1.5 px-0 text-xs text-muted-foreground hover:text-foreground">
          <Plus className="size-3" />
          New Project
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4">
          <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Projects</p>
          <div className="flex flex-col gap-1">
            {projects.map((p) => (
              <button
                key={p.id}
                type="button"
                className={cn(
                  'rounded-md px-2 py-1.5 text-left text-xs transition-colors',
                  p.active ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        <Separator />

        <div className="p-4">
          <div className="mb-2 flex items-center gap-2">
            <Bot className="size-3.5 text-muted-foreground" />
            <span className="text-xs font-medium text-foreground">Agents</span>
          </div>
          <div className="flex flex-col gap-2">
            {agents.map((agent) => (
              <div key={agent.id} className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">{agent.name}</span>
                <span
                  className={cn(
                    'size-1.5 rounded-full',
                    agent.status === 'active' ? 'bg-status-validated' : 'bg-border',
                  )}
                  aria-label={agent.status}
                />
              </div>
            ))}
          </div>
        </div>

        <Separator />

        <div className="p-4">
          <p className="mb-3 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Integrations</p>
          <div className="flex flex-col gap-2">
            {integrations.map((int) => (
              <IntegrationRow key={int.id} label={int.label} connected={int.connected} icon={getIntegrationIcon(int.id)} />
            ))}
          </div>
        </div>
      </ScrollArea>

      <div className="border-t border-border p-3">
        <div className="flex flex-col gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 justify-start gap-2 px-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setJournalOpen(true)}
          >
            <History className="size-3.5" />
            Decision Journal
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 justify-start gap-2 px-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setExportOpen(true)}
          >
            <Download className="size-3.5" />
            Export Workspace
          </Button>
          <Button variant="ghost" size="sm" className="h-8 justify-start gap-2 px-2 text-xs text-muted-foreground hover:text-foreground">
            <Settings className="size-3.5" />
            Settings
          </Button>
        </div>
      </div>
    </aside>
  )
}

function getIntegrationIcon(id: string) {
  switch (id) {
    case 'github':
      return GitBranch
    case 'posthog':
      return LineChart
    case 'gmail':
      return Mail
    case 'slack':
      return MessageSquare
    case 'gummysearch':
      return Search
    case 'reddit':
      return MessageSquare
    default:
      return GitBranch
  }
}

function IntegrationRow({
  icon: Icon,
  label,
  connected,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  connected: boolean
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className="size-3.5 text-muted-foreground" />
        <span className="text-xs text-foreground">{label}</span>
      </div>
      <span
        className={cn('size-1.5 rounded-full', connected ? 'bg-status-validated' : 'bg-border')}
        aria-label={connected ? 'Connected' : 'Not connected'}
      />
    </div>
  )
}
