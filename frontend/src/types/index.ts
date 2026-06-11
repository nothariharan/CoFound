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
  | 'custom_research'

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
  parent_node_id?: string
  research_history: ResearchHistoryEntry[]
  pain_points?: { label: string; percentage: number }[]
  overview?: string
}

export interface ResearchHistoryEntry {
  task_id?: string
  task: string
  status?: 'running' | 'accepted' | 'partial' | 'failed' | string
  score?: number
  reason?: string
  timestamp?: string
  attempt?: number
  query?: string
  tools?: string[]
  result?: {
    summary?: string
    sources?: string[]
    items?: Array<{
      source?: string
      origin?: string
      title?: string
      url?: string | null
      snippet?: string
    }>
  }
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
  nodeType?: string
  nodeId?: string
}

export interface AgentInfo {
  id: string
  name: string
  status: 'active' | 'idle' | 'offline'
  node_id?: string
  parentId?: string
  nodeType?: NodeType
}

export type IntegrationStatus = 'connected' | 'available' | 'coming_soon'

export interface IntegrationInfo {
  id: string
  label: string
  connected: boolean
  status: IntegrationStatus
  description: string
  unlocks?: string
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
  actionsTaken?: Array<{ tool: string; summary: string }>
}

export type VoiceState = 'idle' | 'listening' | 'transcribing' | 'thinking' | 'speaking'

export interface UiAction {
  type: string
  payload?: Record<string, string>
}

export interface OrchestratorChatResult {
  reply: string
  speaking_text?: string
  actions_taken?: Array<{ tool: string; summary: string }>
  ui_actions?: UiAction[]
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

