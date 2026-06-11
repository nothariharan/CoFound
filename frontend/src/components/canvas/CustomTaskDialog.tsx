import { useMemo, useState } from 'react'
import type { NodeType } from '@/types'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

const TARGETABLE_TYPES: NodeType[] = [
  'audience',
  'market_intelligence',
  'competitors',
  'revenue',
  'product_vision',
  'tech_stack',
]

interface CustomTaskDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CustomTaskDialog({ open, onOpenChange }: CustomTaskDialogProps) {
  const workspace = useWorkspaceStore((s) => s.workspace)
  const setSelectedNodeId = useWorkspaceStore((s) => s.setSelectedNodeId)
  const { spawnCustomTask } = useAgentActions()
  const { fetchWorkspace } = useWorkspace()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [nodeType, setNodeType] = useState<NodeType | ''>('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const options = useMemo(() => {
    return (workspace?.nodes ?? [])
      .filter((node) => TARGETABLE_TYPES.includes(node.type))
      .map((node) => ({
        value: node.type,
        label: node.title,
        disabled: node.status === 'locked' || node.active_agents.length > 0,
      }))
  }, [workspace?.nodes])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!workspace?.idea_id || !title.trim() || !description.trim()) return

    setSubmitting(true)
    setError(null)
    try {
      await spawnCustomTask(workspace.idea_id, title.trim(), description.trim(), nodeType || undefined)
      await fetchWorkspace(workspace.idea_id)
      setSelectedNodeId(null)
      setTitle('')
      setDescription('')
      setNodeType('')
      onOpenChange(false)
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to spawn custom task')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Spawn Custom Agent</DialogTitle>
          <DialogDescription>
            Give the orchestrator an external task. It will assign a dedicated agent and stream progress in Activity.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label htmlFor="custom-task-title" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Task title
            </label>
            <Input
              id="custom-task-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Research government API partners"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="custom-task-description" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              What should the agent do?
            </label>
            <Textarea
              id="custom-task-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Find passport renewal APIs, pricing, and integration requirements for India."
              rows={4}
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="custom-task-node" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Attach to graph area (optional)
            </label>
            <select
              id="custom-task-node"
              value={nodeType}
              onChange={(event) => setNodeType(event.target.value as NodeType | '')}
              className="h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground"
            >
              <option value="">Let orchestrator choose</option>
              {options.map((option) => (
                <option key={option.value} value={option.value} disabled={option.disabled}>
                  {option.label}
                  {option.disabled ? ' (busy or locked)' : ''}
                </option>
              ))}
            </select>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || !title.trim() || !description.trim()}>
              {submitting ? 'Spawning...' : 'Spawn Agent'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
