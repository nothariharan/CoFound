import { useWorkspaceStore } from '@/store/workspaceStore'
import { MOCK_JOURNAL } from '@/mock/workspace'
import { formatRelativeTime } from '@/utils/formatters'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

export function DecisionJournal() {
  const { journalOpen, setJournalOpen, setSelectedNodeId, workspace } = useWorkspaceStore()

  return (
    <Dialog open={journalOpen} onOpenChange={setJournalOpen}>
      <DialogContent className="max-h-[80vh] max-w-lg">
        <DialogHeader>
          <DialogTitle>Decision Journal</DialogTitle>
          <DialogDescription>
            Every graph mutation with reasons, evidence, and timestamps.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="flex flex-col gap-4">
            {MOCK_JOURNAL.map((entry, i) => {
              const node = workspace?.nodes.find((n) => n.type === entry.node_type)
              return (
                <div key={i}>
                  <button
                    type="button"
                    className="w-full text-left"
                    onClick={() => {
                      if (node) {
                        setSelectedNodeId(node.node_id)
                        setJournalOpen(false)
                      }
                    }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <Badge variant="outline">{entry.node_type.replace('_', ' ')}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatRelativeTime(entry.timestamp)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm font-medium text-foreground">{entry.event.replace('_', ' ')}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{entry.reason}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {entry.evidence.map((e) => (
                        <span key={e} className="rounded border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
                          {e}
                        </span>
                      ))}
                    </div>
                    <p className="mt-2 text-xs tabular-nums text-muted-foreground">
                      {entry.confidence_before}% → {entry.confidence_after}%
                    </p>
                  </button>
                  {i < MOCK_JOURNAL.length - 1 && <Separator className="mt-4" />}
                </div>
              )
            })}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
