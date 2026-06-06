import { Download } from 'lucide-react'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { MOCK_EXPORT_FILES } from '@/mock/workspace'
import { USE_MOCK } from '@/config/env'
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
  const { exportOpen, setExportOpen, workspace } = useWorkspaceStore()

  const handleExport = async () => {
    if (!USE_MOCK && workspace?.idea_id) {
      const res = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspace.idea_id }),
      })
      if (!res.ok) return
      const data = await res.json()
      if (typeof data.export_url === 'string') {
        window.location.assign(data.export_url)
        setExportOpen(false)
      }
      return
    }

    const content = MOCK_EXPORT_FILES.map((f) => `- ${f}`).join('\n')
    const blob = new Blob([`CoFounder Export\n\n${content}`], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'cofounder-export.txt'
    a.click()
    URL.revokeObjectURL(url)
    setExportOpen(false)
  }

  return (
    <Dialog open={exportOpen} onOpenChange={setExportOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export Workspace</DialogTitle>
          <DialogDescription>
            Download your startup knowledge graph as a scaffold package.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-2 py-2">
          {MOCK_EXPORT_FILES.map((file) => (
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
          <Button onClick={handleExport}>Download</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
