import { useMemo } from 'react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'

export function SettingsDialog() {
  const { settingsOpen, setSettingsOpen, workspace, integrations, setSelectedNodeId } = useWorkspaceStore()

  const gaps = useMemo(() => {
    return (workspace?.nodes ?? []).filter(
      (node) => node.type !== 'core_idea' && (node.confidence < 70 || node.sources.length === 0),
    )
  }, [workspace?.nodes])

  const known = useMemo(() => {
    return (workspace?.nodes ?? [])
      .filter((node) => node.confidence > 0 || node.summary || node.agent_notes)
      .map((node) => ({
        type: node.type.replace(/_/g, ' '),
        summary: node.agent_notes || node.summary,
        confidence: node.confidence,
      }))
  }, [workspace?.nodes])

  return (
    <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
      <DialogContent className="max-h-[84vh] max-w-2xl">
        <DialogHeader>
          <DialogTitle>Workspace Settings</DialogTitle>
          <DialogDescription>
            Live context the agents know, missing evidence, and connected data sources for this workspace.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[66vh] pr-4">
          {!workspace && <p className="text-sm text-muted-foreground">No active workspace.</p>}
          {workspace && (
            <div className="flex flex-col gap-6">
              <section>
                <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Project</p>
                <h3 className="mt-1 text-base font-semibold text-foreground">{workspace.workspace_name}</h3>
                <p className="mt-1 text-xs text-muted-foreground">Workspace ID: {workspace.idea_id}</p>
              </section>

              <section>
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Integrations</p>
                <div className="grid grid-cols-2 gap-2">
                  {integrations.map((integration) => (
                    <div key={integration.id} className="rounded-md border border-border p-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm text-foreground">{integration.label}</span>
                        <Badge variant={integration.connected ? 'success' : integration.status === 'coming_soon' ? 'outline' : 'warning'}>
                          {integration.connected ? 'connected' : integration.status.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{integration.description}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Knowledge Graph</p>
                <p className="mb-3 text-xs text-muted-foreground">
                  Current workspace graph with status, confidence, sources, and latest agent activity. Click a node to open it.
                </p>
                <div className="flex flex-col gap-2">
                  {workspace.nodes.map((node) => (
                    <button
                      key={node.node_id}
                      type="button"
                      onClick={() => {
                        setSelectedNodeId(node.node_id)
                        setSettingsOpen(false)
                      }}
                      className="rounded-md border border-border p-3 text-left transition-colors hover:border-primary/40 hover:bg-primary/5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium text-foreground">{node.title}</p>
                        <Badge variant={node.status === 'validated' ? 'success' : node.status === 'needs_work' ? 'warning' : node.status === 'blocking' ? 'destructive' : 'secondary'}>
                          {node.status.replace(/_/g, ' ')}
                        </Badge>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
                        <span>{node.confidence}% confidence</span>
                        <span>{node.source_pills.length} sources</span>
                        {node.active_agents.length > 0 && <span>{node.active_agents.length} active agent(s)</span>}
                      </div>
                      <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                        {node.research_history.at(-1)?.result?.summary ||
                          node.research_history.at(-1)?.reason ||
                          node.agent_notes ||
                          node.summary ||
                          'No research yet.'}
                      </p>
                    </button>
                  ))}
                </div>
              </section>

              <section>
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Confidence Map</p>
                <div className="flex flex-col gap-2">
                  {workspace.nodes.map((node) => (
                    <div key={node.node_id}>
                      <div className="mb-1 flex items-center justify-between text-xs">
                        <span className="capitalize text-foreground">{node.type.replace(/_/g, ' ')}</span>
                        <span className="tabular-nums text-muted-foreground">{node.confidence}%</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${node.confidence}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Knowledge Gaps</p>
                {gaps.length === 0 && <p className="text-sm text-muted-foreground">No major gaps visible in the current graph.</p>}
                <div className="flex flex-col gap-2">
                  {gaps.map((node) => (
                    <div key={node.node_id} className="rounded-md border border-border p-2">
                      <p className="text-sm font-medium capitalize text-foreground">{node.type.replace(/_/g, ' ')}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {node.confidence < 70 ? `Confidence is ${node.confidence}%. ` : ''}
                        {node.sources.length === 0 ? 'No accepted sources yet. ' : ''}
                        {node.research_history?.at(-1)?.reason ?? node.agent_notes}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">What Agents Know</p>
                <div className="flex flex-col gap-2">
                  {known.map((item) => (
                    <div key={item.type} className="rounded-md border border-border p-2">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium capitalize text-foreground">{item.type}</p>
                        <span className="text-xs tabular-nums text-muted-foreground">{item.confidence}%</span>
                      </div>
                      <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">{item.summary || 'No summary yet.'}</p>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
