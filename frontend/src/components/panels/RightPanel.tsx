import { useState } from 'react'
import { Play, X } from 'lucide-react'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { OrchestratorPanel } from '@/components/panels/OrchestratorPanel'
import { NodeDetails } from '@/components/panels/NodeDetails'
import { NodeHistory } from '@/components/panels/NodeHistory'
import { NodeChat } from '@/components/panels/NodeChat'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { statusBadgeVariant, statusLabels } from '@/utils/nodeColors'

export function RightPanel() {
  const { workspace, getSelectedNode, setSelectedNodeId } = useWorkspaceStore()
  const { researchNode } = useAgentActions()
  const { fetchWorkspace } = useWorkspace()
  const [approving, setApproving] = useState(false)
  const [approvalError, setApprovalError] = useState<string | null>(null)
  const selectedNode = getSelectedNode()

  if (!selectedNode) {
    return <OrchestratorPanel />
  }

  const canApproveResearch =
    Boolean(workspace?.idea_id) &&
    selectedNode.type !== 'core_idea' &&
    selectedNode.status !== 'locked' &&
    selectedNode.active_agents.length === 0
  const isResearching = selectedNode.active_agents.length > 0

  const handleApproveResearch = async () => {
    if (!workspace?.idea_id || !canApproveResearch) return
    setApproving(true)
    setApprovalError(null)
    try {
      await researchNode(workspace.idea_id, selectedNode.type)
      await fetchWorkspace(workspace.idea_id)
    } catch (error) {
      setApprovalError(error instanceof Error ? error.message : 'Failed to approve research')
    } finally {
      setApproving(false)
    }
  }

  return (
    <aside className="shell-panel flex h-full w-[320px] shrink-0 flex-col border-l border-border bg-card">
      <div className="flex items-start justify-between border-b border-border p-4">
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-semibold text-foreground">{selectedNode.title}</h2>
          <Badge variant={statusBadgeVariant[selectedNode.status]} className="mt-1">
            {statusLabels[selectedNode.status]}
          </Badge>
          {canApproveResearch && (
            <div className="mt-3">
              <Button
                variant="default"
                size="sm"
                className="gap-2"
                onClick={() => void handleApproveResearch()}
                disabled={approving}
              >
                <Play className="size-3.5" />
                {approving ? 'Starting...' : `Approve ${selectedNode.title} research`}
              </Button>
            </div>
          )}
          {isResearching && (
            <p className="mt-3 rounded-md border border-border bg-background/60 px-3 py-2 text-xs text-muted-foreground">
              Research running. Watch the History tab for attempts, critique scores, and evidence as it streams in.
            </p>
          )}
          {approvalError && <p className="mt-2 text-xs text-destructive">{approvalError}</p>}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="size-8 text-muted-foreground"
          onClick={() => setSelectedNodeId(null)}
          aria-label="Close panel"
        >
          <X className="size-4" />
        </Button>
      </div>

      <Tabs defaultValue="chat" className="flex min-h-0 flex-1 flex-col">
        <TabsList className="w-full justify-start px-4">
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="sources">Sources ({selectedNode.source_pills.length})</TabsTrigger>
          <TabsTrigger value="notes">Notes</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <NodeChat node={selectedNode} />
        </TabsContent>
        <TabsContent value="sources" className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <NodeDetails node={selectedNode} />
        </TabsContent>
        <TabsContent value="notes" className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="p-4 text-sm text-muted-foreground">
            {selectedNode.agent_notes || 'No notes yet.'}
          </div>
        </TabsContent>
        <TabsContent value="history" className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <NodeHistory node={selectedNode} />
        </TabsContent>
      </Tabs>
    </aside>
  )
}
