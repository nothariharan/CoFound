import { X } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { AgentFeed } from '@/components/panels/AgentFeed'
import { NodeDetails } from '@/components/panels/NodeDetails'
import { NodeChat } from '@/components/panels/NodeChat'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { statusBadgeVariant, statusLabels } from '@/utils/nodeColors'

export function RightPanel() {
  const { getSelectedNode, setSelectedNodeId } = useWorkspaceStore()
  const selectedNode = getSelectedNode()

  if (!selectedNode) {
    return (
      <aside className="shell-panel flex h-full w-[360px] shrink-0 flex-col border-l border-border bg-card">
        <AgentFeed />
      </aside>
    )
  }

  return (
    <aside className="shell-panel flex h-full w-[360px] shrink-0 flex-col border-l border-border bg-card">
      <div className="flex items-start justify-between border-b border-border p-4">
        <div>
          <h2 className="text-base font-semibold text-foreground">{selectedNode.title}</h2>
          <Badge variant={statusBadgeVariant[selectedNode.status]} className="mt-1">
            {statusLabels[selectedNode.status]}
          </Badge>
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
          <AgentFeed />
        </TabsContent>
      </Tabs>
    </aside>
  )
}
