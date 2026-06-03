export type NodeStatus = 'validated' | 'needs_work' | 'blocking' | 'locked'

export type NodeType =
  | 'core_idea'
  | 'audience'
  | 'market_intelligence'
  | 'competitors'
  | 'revenue'
  | 'product_vision'
  | 'tech_stack'
  | 'build'
  | 'launch'
  | 'observe'
  | 'growth'

export interface SourcePill {
  label: string
  count: number
  url?: string
}

export interface GraphNode {
  node_id: string
  type: NodeType
  confidence: number
  status: NodeStatus
  sources: string[]
  source_pills: SourcePill[]
  agent_notes: string
  title: string
  summary: string
  last_updated: string
  active_agents: string[]
}

export interface Workspace {
  idea_id: string
  workspace_name: string
  nodes: GraphNode[]
}

export interface FeedMessage {
  text: string
  type: 'info' | 'ping' | 'error'
}

export type AppPhase = 'intake' | 'dashboard'

export interface TodayPriority {
  action: string
  reason: string
  estimatedTime?: string
}
