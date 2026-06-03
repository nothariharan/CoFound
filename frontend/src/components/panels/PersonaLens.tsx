import { useState } from 'react'
import type { GraphNode } from '../../types'

const PERSONAS = [
  { id: 'paul_graham', name: 'Paul Graham' },
  { id: 'steve_jobs', name: 'Steve Jobs' },
  { id: 'andy_grove', name: 'Andy Grove' },
  { id: 'gary_keller', name: 'Gary Keller' },
]

interface PersonaLensProps {
  node: GraphNode
}

export function PersonaLens({ node }: PersonaLensProps) {
  const [selected, setSelected] = useState('')
  const [response, setResponse] = useState<string | null>(null)

  const handleEvaluate = () => {
    if (!selected) return
    const persona = PERSONAS.find((p) => p.id === selected)
    setResponse(
      `${persona?.name} lens on ${node.title}: evaluation will run once agents are connected.`,
    )
  }

  return (
    <div className="p-4">
      <p className="mb-3 text-[10px] font-medium uppercase tracking-wide text-[#737373]">
        Persona Lens
      </p>
      <select
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        className="mb-3 w-full rounded border border-[#e5e5e5] px-3 py-2 text-sm focus:border-[#2563eb] focus:outline-none"
      >
        <option value="">Select persona...</option>
        {PERSONAS.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <button
        onClick={handleEvaluate}
        disabled={!selected}
        className="w-full rounded bg-[#2563eb] py-2 text-sm font-medium text-white disabled:opacity-40"
      >
        Evaluate
      </button>
      {response && (
        <p className="mt-3 text-sm text-[#737373]">{response}</p>
      )}
    </div>
  )
}
