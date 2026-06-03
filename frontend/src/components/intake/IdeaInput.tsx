import { useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { useWorkspace } from '../../hooks/useWorkspace'

export function IdeaInput() {
  const [idea, setIdea] = useState('')
  const { createWorkspace, loading, error } = useWorkspace()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!idea.trim() || loading) return
    await createWorkspace(idea.trim())
  }

  return (
    <div className="flex h-full min-h-screen flex-col items-center justify-center bg-[#fafafa] px-6">
      <div className="w-full max-w-xl">
        <p className="mb-2 text-sm font-medium tracking-wide text-[#737373] uppercase">
          CoFounder
        </p>
        <h1 className="mb-8 text-2xl font-semibold text-[#171717]">
          What are we building?
        </h1>
        <form onSubmit={handleSubmit}>
          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="Describe your startup idea in a sentence or two..."
            rows={4}
            className="mb-4 w-full resize-none rounded border border-[#e5e5e5] bg-white px-4 py-3 text-[#171717] placeholder:text-[#a3a3a3] focus:border-[#2563eb] focus:outline-none"
            autoFocus
          />
          {error && (
            <p className="mb-3 text-sm text-[#dc2626]">{error}</p>
          )}
          <button
            type="submit"
            disabled={!idea.trim() || loading}
            className="inline-flex items-center gap-2 rounded bg-[#2563eb] px-5 py-2.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? 'Starting...' : 'Start'}
            {!loading && <ArrowRight size={16} strokeWidth={2} />}
          </button>
        </form>
      </div>
    </div>
  )
}
