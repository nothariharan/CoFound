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
  pain_points?: { label: string; percentage: number }[]
  overview?: string
}

export interface Workspace {
  idea_id: string
  workspace_name: string
  nodes: GraphNode[]
}

export interface FeedMessage {
  text: string
  type: 'info' | 'critique' | 'error' | 'done' | 'ping'
  node_id?: string
  score?: number
}

export type AppPhase = 'intake' | 'dashboard'

export interface TodayPriority {
  action: string
  reason: string
  estimatedTime?: string
  impact?: string
}

export interface AgentInfo {
  id: string
  name: string
  status: 'active' | 'idle' | 'offline'
  node_id?: string
}

export interface IntegrationInfo {
  id: string
  label: string
  connected: boolean
}

export interface ProjectInfo {
  id: string
  name: string
  active: boolean
}

export interface ChatMessage {
  role: 'user' | 'agent'
  text: string
  agentName?: string
}

export interface JournalEntry {
  timestamp: string
  node_type: NodeType
  event: string
  reason: string
  evidence: string[]
  confidence_before: number
  confidence_after: number
}

export interface DemoState {
  pivotBlurredNodes: string[]
  stage: number
}
