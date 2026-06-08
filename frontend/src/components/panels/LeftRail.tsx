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
import { useEffect, useMemo } from 'react'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useGoHome } from '@/hooks/useGoHome'
import { INTEGRATION_CATALOG, mergeIntegrationStatus } from '@/config/integrations'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { IntegrationConnectDialog } from '@/components/integrations/IntegrationConnectDialog'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { IntegrationInfo } from '@/types'

export function LeftRail() {
  const goHome = useGoHome()
  const {
    workspace,
    agents,
    integrations,
    projects,
    mode,
    setJournalOpen,
    setExportOpen,
    setIntegrations,
    integrationDialogId,
    setIntegrationDialogId,
  } = useWorkspaceStore()
  const { fetchIntegrations } = useAgentActions()
  const isDemo = mode === 'demo'

  const connectTarget = useMemo(
    () => integrations.find((i) => i.id === integrationDialogId) ?? null,
    [integrations, integrationDialogId],
  )

  useEffect(() => {
    if (!workspace?.idea_id || isDemo) return
    void fetchIntegrations(workspace.idea_id)
      .then((status) => {
        setIntegrations(mergeIntegrationStatus(INTEGRATION_CATALOG.map((i) => ({ ...i })), status))
      })
      .catch(() => {})
  }, [workspace?.idea_id, fetchIntegrations, setIntegrations, isDemo])

  const projectList = useMemo(() => {
    if (isDemo) return projects
    if (!workspace) return []
    return [{ id: workspace.idea_id, name: workspace.workspace_name, active: true }]
  }, [isDemo, projects, workspace])

  const handleIntegrationClick = (integration: IntegrationInfo) => {
    if (integration.status === 'coming_soon') return
    if (integration.status === 'connected' && integration.id !== 'reddit') return
    if (integration.id === 'github' || integration.id === 'posthog') {
      setIntegrationDialogId(integration.id)
    }
  }

  return (
    <>
      <aside className="shell-panel flex h-full w-[220px] shrink-0 flex-col border-r border-border bg-card">
        <div className="border-b border-border p-4">
          <button
            type="button"
            onClick={goHome}
            className="text-sm font-semibold text-foreground transition-colors hover:text-primary"
          >
            CoFound
          </button>
        </div>

        <div className="border-b border-border p-4">
          <p className="mb-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">Project</p>
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-md py-1 text-sm font-medium text-foreground hover:text-primary"
            aria-label="Switch project"
          >
            <span className="truncate">{workspace?.workspace_name ?? 'Workspace'}</span>
            <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" />
          </button>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2 h-8 gap-1.5 px-0 text-xs text-muted-foreground hover:text-foreground"
            onClick={goHome}
          >
            <Plus className="size-3" />
            New Project
          </Button>
        </div>

        <ScrollArea className="flex-1">
          {projectList.length > 0 && (
            <div className="p-4">
              <p className="mb-2 text-[9px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                Projects
              </p>
              <div className="flex flex-col gap-1">
                {projectList.map((p) => (
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
          )}

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
                      agent.status === 'active' ? 'bg-status-validated' : 'bg-muted',
                    )}
                    aria-label={agent.status}
                  />
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div className="p-4" data-onboarding="integrations">
            <p className="mb-3 text-[9px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
              Integrations
            </p>
            <div className="flex flex-col gap-2">
              {integrations.map((int) => (
                <IntegrationRow
                  key={int.id}
                  label={int.label}
                  connected={int.connected}
                  status={int.status}
                  icon={getIntegrationIcon(int.id)}
                  onClick={() => handleIntegrationClick(int)}
                />
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

      <IntegrationConnectDialog
        integration={connectTarget}
        open={!!integrationDialogId && !!connectTarget}
        onOpenChange={(open) => {
          if (!open) setIntegrationDialogId(null)
        }}
      />
    </>
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
  status,
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  connected: boolean
  status: IntegrationInfo['status']
  onClick: () => void
}) {
  const isComingSoon = status === 'coming_soon'
  const isClickable = !isComingSoon && (status === 'available' || label === 'Reddit')

  return (
    <button
      type="button"
      disabled={isComingSoon || (connected && label !== 'Reddit')}
      onClick={onClick}
      className={cn(
        'flex w-full items-center justify-between rounded-md px-1 py-1 text-left transition-colors',
        isClickable && !connected && 'hover:bg-accent/50',
        isComingSoon && 'cursor-not-allowed opacity-60',
        connected && label !== 'Reddit' && 'cursor-default',
      )}
    >
      <div className="flex items-center gap-2">
        <Icon className="size-3.5 text-muted-foreground" />
        <span className="text-xs text-foreground">{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        {isComingSoon && (
          <Badge variant="outline" className="h-4 px-1.5 text-[9px]">
            Soon
          </Badge>
        )}
        <span
          className={cn('size-1.5 rounded-full', connected ? 'bg-status-validated' : 'bg-border')}
          aria-label={connected ? 'Connected' : 'Not connected'}
        />
      </div>
    </button>
  )
}
