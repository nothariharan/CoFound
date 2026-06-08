import { useState } from 'react'
import { toast } from 'sonner'
import type { IntegrationInfo } from '@/types'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspace } from '@/hooks/useWorkspace'
import { INTEGRATION_CATALOG, mergeIntegrationStatus } from '@/config/integrations'
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

interface IntegrationConnectDialogProps {
  integration: IntegrationInfo | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function IntegrationConnectDialog({
  integration,
  open,
  onOpenChange,
}: IntegrationConnectDialogProps) {
  const { workspace, setIntegrations } = useWorkspaceStore()
  const { connectGithub, connectPosthog, fetchIntegrations } = useAgentActions()
  const { fetchWorkspace } = useWorkspace()
  const [repo, setRepo] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [projectId, setProjectId] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClose = (next: boolean) => {
    if (!next) {
      setRepo('')
      setAccessToken('')
      setProjectId('')
      setApiKey('')
      setError(null)
    }
    onOpenChange(next)
  }

  const refreshAfterConnect = async () => {
    if (!workspace?.idea_id) return
    const status = await fetchIntegrations(workspace.idea_id)
    setIntegrations(mergeIntegrationStatus(INTEGRATION_CATALOG.map((i) => ({ ...i })), status))
    await fetchWorkspace(workspace.idea_id)
  }

  const handleConnect = async () => {
    if (!workspace?.idea_id || !integration) return
    setLoading(true)
    setError(null)
    try {
      if (integration.id === 'github') {
        if (!repo.trim()) {
          setError('Enter a repository in owner/name format.')
          return
        }
        await connectGithub(workspace.idea_id, repo.trim(), accessToken.trim() || undefined)
        toast.success('GitHub connected', {
          description: 'Build node is now available for agent tracking.',
        })
      } else if (integration.id === 'posthog') {
        if (!projectId.trim() || !apiKey.trim()) {
          setError('Project ID and API key are required.')
          return
        }
        await connectPosthog(workspace.idea_id, projectId.trim(), apiKey.trim())
        toast.success('PostHog connected', {
          description: 'Observe node is now available for funnel monitoring.',
        })
      }
      await refreshAfterConnect()
      handleClose(false)
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Connection failed'
      setError(message)
      toast.error('Connection failed', { description: message })
    } finally {
      setLoading(false)
    }
  }

  if (!integration) return null

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Connect {integration.label}</DialogTitle>
          <DialogDescription>{integration.description}</DialogDescription>
        </DialogHeader>

        {integration.unlocks && (
          <div className="rounded-md border border-border bg-surface-elevated px-3 py-2 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Unlocks:</span> {integration.unlocks}
          </div>
        )}

        {integration.id === 'github' && (
          <div className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Repository (owner/name)</label>
              <Input
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="your-org/your-repo"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">
                Access token (optional — uses server env if omitted)
              </label>
              <Input
                type="password"
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder="ghp_..."
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Agents will pull recent commits and summarize build progress on your graph.
            </p>
          </div>
        )}

        {integration.id === 'posthog' && (
          <div className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Project ID</label>
              <Input
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                placeholder="12345"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">API key</label>
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="phc_..."
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Agents will monitor funnel drops and recommend growth actions automatically.
            </p>
          </div>
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}

        <DialogFooter>
          <Button variant="outline" onClick={() => handleClose(false)}>
            Cancel
          </Button>
          <Button onClick={() => void handleConnect()} disabled={loading}>
            {loading ? 'Connecting...' : 'Connect'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
