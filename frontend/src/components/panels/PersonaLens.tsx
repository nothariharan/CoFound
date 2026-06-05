import type { GraphNode } from '@/types'

interface PersonaLensProps {
  node: GraphNode
}

export function PersonaLens({ node }: PersonaLensProps) {
  return (
    <div className="p-4 text-sm text-muted-foreground">
      Persona lens for <span className="text-foreground">{node.title}</span> — available after audience research completes.
    </div>
  )
}
