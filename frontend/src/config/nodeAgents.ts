import type { NodeType } from '@/types'

export interface NodeAgentConfig {
  id: string
  name: string
  nodeType: NodeType
}

export const NODE_AGENT_CONFIG: Record<NodeType, NodeAgentConfig> = {
  core_idea: { id: 'agent_core_idea', name: 'Idea Framer', nodeType: 'core_idea' },
  audience: { id: 'agent_audience', name: 'Audience Scout', nodeType: 'audience' },
  market_intelligence: { id: 'agent_market', name: 'Market Analyst', nodeType: 'market_intelligence' },
  competitors: { id: 'agent_competitors', name: 'Competitor Tracker', nodeType: 'competitors' },
  revenue: { id: 'agent_revenue', name: 'Revenue Modeler', nodeType: 'revenue' },
  product_vision: { id: 'agent_product', name: 'Product Strategist', nodeType: 'product_vision' },
  tech_stack: { id: 'agent_tech', name: 'Tech Architect', nodeType: 'tech_stack' },
  build: { id: 'agent_build', name: 'Build Engineer', nodeType: 'build' },
  launch: { id: 'agent_launch', name: 'Launch Coordinator', nodeType: 'launch' },
  observe: { id: 'agent_observe', name: 'Signal Observer', nodeType: 'observe' },
  growth: { id: 'agent_growth', name: 'Growth Agent', nodeType: 'growth' },
}

const AGENT_ID_TO_CONFIG = Object.fromEntries(
  Object.values(NODE_AGENT_CONFIG).map((config) => [config.id, config]),
) as Record<string, NodeAgentConfig>

export function getNodeAgentConfig(type: NodeType): NodeAgentConfig {
  return NODE_AGENT_CONFIG[type]
}

export function resolveAgentDisplayName(agentId: string): string {
  if (agentId === 'orchestrator') return 'Orchestrator'
  const config = AGENT_ID_TO_CONFIG[agentId]
  if (config) return config.name
  return agentId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function resolveAgentIdForNodeType(type: NodeType): string {
  return NODE_AGENT_CONFIG[type].id
}
