import { ArrowRight } from 'lucide-react'
import { useState } from 'react'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useIntakeAnimation } from '@/hooks/useAnimations'
import { DEMO_IDEA } from '@/mock/workspace'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

export function IdeaInput() {
  const [idea, setIdea] = useState('')
  const { createWorkspace, loading, error } = useWorkspace()
  const containerRef = useIntakeAnimation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!idea.trim() || loading) return
    await createWorkspace(idea.trim())
  }

  const handleDemo = async () => {
    setIdea(DEMO_IDEA)
    await createWorkspace(DEMO_IDEA)
  }

  return (
    <div
      ref={containerRef}
      className="flex h-full min-h-dvh flex-col items-center justify-center bg-background px-6"
    >
      <div className="w-full max-w-xl">
        <p className="intake-animate mb-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          CoFound
        </p>
        <h1 className="intake-animate mb-2 text-3xl font-semibold tracking-tight text-foreground">
          What are we building?
        </h1>
        <p className="intake-animate mb-8 text-sm text-muted-foreground">
          Describe your startup idea. AI agents will research, validate, and build your company graph.
        </p>
        <form onSubmit={handleSubmit} className="intake-animate">
          <Textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="Describe your startup idea in a sentence or two..."
            rows={4}
            className="mb-4 resize-none"
            autoFocus
          />
          {error && <p className="mb-3 text-sm text-destructive">{error}</p>}
          <div className="flex items-center gap-3">
            <Button type="submit" disabled={!idea.trim() || loading} className="gap-2">
              {loading ? 'Starting...' : 'Start'}
              {!loading && <ArrowRight className="size-4" />}
            </Button>
            <Button type="button" variant="outline" onClick={handleDemo} disabled={loading}>
              Load demo
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
