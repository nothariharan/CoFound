import type { NodeType } from '@/types'

export interface NodeLayout {
  node_id: string
  type: NodeType
  x: number
  y: number
}

export const NODE_LAYOUT: NodeLayout[] = [
  { node_id: 'node-core', type: 'core_idea', x: 400, y: 0 },
  { node_id: 'node-audience', type: 'audience', x: 80, y: 200 },
  { node_id: 'node-market', type: 'market_intelligence', x: 400, y: 200 },
  { node_id: 'node-competitors', type: 'competitors', x: 720, y: 200 },
  { node_id: 'node-revenue', type: 'revenue', x: 80, y: 420 },
  { node_id: 'node-product', type: 'product_vision', x: 400, y: 420 },
  { node_id: 'node-tech', type: 'tech_stack', x: 720, y: 420 },
  { node_id: 'node-build', type: 'build', x: 400, y: 640 },
  { node_id: 'node-launch', type: 'launch', x: 160, y: 820 },
  { node_id: 'node-observe', type: 'observe', x: 400, y: 820 },
  { node_id: 'node-growth', type: 'growth', x: 640, y: 820 },
]

export const NODE_EDGES: { source: string; target: string }[] = [
  { source: 'node-core', target: 'node-audience' },
  { source: 'node-core', target: 'node-market' },
  { source: 'node-core', target: 'node-competitors' },
  { source: 'node-audience', target: 'node-revenue' },
  { source: 'node-market', target: 'node-product' },
  { source: 'node-competitors', target: 'node-tech' },
  { source: 'node-revenue', target: 'node-build' },
  { source: 'node-product', target: 'node-build' },
  { source: 'node-tech', target: 'node-build' },
  { source: 'node-build', target: 'node-launch' },
  { source: 'node-build', target: 'node-observe' },
  { source: 'node-build', target: 'node-growth' },
]

export function getNodePosition(nodeId: string, nodeType?: NodeType): { x: number; y: number } {
  const byId = NODE_LAYOUT.find((n) => n.node_id === nodeId)
  if (byId) return { x: byId.x, y: byId.y }
  if (nodeType) {
    const byType = NODE_LAYOUT.find((n) => n.type === nodeType)
    if (byType) return { x: byType.x, y: byType.y }
  }
  return { x: 0, y: 0 }
}
