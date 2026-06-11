import { useState } from 'react'
import { Download } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useAgentActions } from '@/hooks/useAgentActions'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export function ExportModal() {
  const { exportOpen, setExportOpen, workspace, setHasExported } = useWorkspaceStore()
  const { requestExport } = useAgentActions()
  const [files, setFiles] = useState<string[]>([])
  const [exportUrl, setExportUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadExportPreview = async () => {
    if (!workspace?.idea_id) return
    setLoading(true)
    setError(null)
    try {
      const result = await requestExport(workspace.idea_id)
      setFiles(result.files)
      setExportUrl(result.export_url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenChange = (open: boolean) => {
    setExportOpen(open)
    if (open && workspace?.idea_id) {
      void loadExportPreview()
    }
    if (!open) {
      setError(null)
    }
  }

  const handleExport = () => {
    if (exportUrl) {
      window.open(exportUrl, '_blank')
      setHasExported(true)
      setExportOpen(false)
    }
  }

  return (
    <Dialog open={exportOpen} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export Workspace</DialogTitle>
          <DialogDescription>
            Download your startup knowledge graph as a scaffold package.
          </DialogDescription>
        </DialogHeader>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex flex-col gap-2 py-2">
          {files.length === 0 && (
            <p className="text-sm text-muted-foreground">
              {loading ? 'Generating export package...' : 'Open the export to generate files.'}
            </p>
          )}
          {files.map((file) => (
            <div
              key={file}
              className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-foreground"
            >
              <Download className="size-3.5 text-muted-foreground" />
              {file}
            </div>
          ))}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setExportOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={loading || !exportUrl}>
            {loading ? 'Generating...' : 'Download'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
