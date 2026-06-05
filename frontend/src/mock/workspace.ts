import type { GraphNode, JournalEntry, ProjectInfo, Workspace } from '@/types'
import { MOCK_IDEA_ID } from '@/config/env'

const now = () => new Date().toISOString()
const minsAgo = (m: number) => new Date(Date.now() - m * 60_000).toISOString()

function lockedNode(
  id: string,
  type: GraphNode['type'],
  title: string,
  summary: string,
): GraphNode {
  return {
    node_id: id,
    type,
    confidence: 0,
    status: 'locked',
    sources: [],
    source_pills: [],
    agent_notes: '',
    title,
    summary,
    last_updated: now(),
    active_agents: [],
  }
}

export const DEMO_IDEA =
  'AI copilot for busy restaurant owners to manage inventory, staff scheduling, and daily operations'

export const MOCK_PROJECTS: ProjectInfo[] = [
  { id: '1', name: 'GoFounder AI', active: false },
  { id: '2', name: 'Restaurant Copilot', active: true },
  { id: '3', name: 'StudyBuddy', active: false },
  { id: '4', name: 'FinPilot', active: false },
]

export const MOCK_JOURNAL: JournalEntry[] = [
  {
    timestamp: minsAgo(45),
    node_type: 'audience',
    event: 'confidence_updated',
    reason: 'Research committed after critique score 81',
    evidence: ['847 Reddit posts', '23 GummySearch threads'],
    confidence_before: 0,
    confidence_after: 72,
  },
  {
    timestamp: minsAgo(38),
    node_type: 'market_intelligence',
    event: 'confidence_updated',
    reason: 'Market scan completed — pain points ranked',
    evidence: ['312 Reddit posts', '89 Product Hunt reviews'],
    confidence_before: 0,
    confidence_after: 68,
  },
  {
    timestamp: minsAgo(30),
    node_type: 'competitors',
    event: 'confidence_updated',
    reason: 'Competitive landscape mapped',
    evidence: ['14 direct competitors', '6 indirect alternatives'],
    confidence_before: 0,
    confidence_after: 61,
  },
]

export function createCoreIdeaOnly(): Workspace {
  return {
    idea_id: MOCK_IDEA_ID,
    workspace_name: 'Restaurant Copilot',
    nodes: [
      {
        node_id: 'node-core',
        type: 'core_idea',
        confidence: 84,
        status: 'validated',
        sources: ['user_input'],
        source_pills: [],
        agent_notes: 'Strong initial concept with clear target market',
        title: 'Core Idea',
        summary: 'AI copilot for busy restaurant owners',
        last_updated: now(),
        active_agents: [],
        overview:
          'An AI-powered assistant that helps restaurant owners manage inventory, staff scheduling, and daily operations through natural conversation.',
      },
    ],
  }
}

export function createStage2Workspace(): Workspace {
  return {
    idea_id: MOCK_IDEA_ID,
    workspace_name: 'Restaurant Copilot',
    nodes: [
      {
        node_id: 'node-core',
        type: 'core_idea',
        confidence: 84,
        status: 'validated',
        sources: ['user_input'],
        source_pills: [],
        agent_notes: 'Strong initial concept with clear target market',
        title: 'Core Idea',
        summary: 'AI copilot for busy restaurant owners',
        last_updated: minsAgo(60),
        active_agents: [],
      },
      {
        node_id: 'node-audience',
        type: 'audience',
        confidence: 72,
        status: 'needs_work',
        sources: ['reddit', 'gummysearch'],
        source_pills: [
          { label: 'Reddit', count: 847 },
          { label: 'GummySearch', count: 23 },
        ],
        agent_notes: '847 Reddit posts analyzed — independent owners are primary segment',
        title: 'Audience',
        summary: 'Independent restaurant owners, 1-3 locations, 50-200 covers/day',
        last_updated: minsAgo(45),
        active_agents: ['researcher_1'],
      },
      {
        node_id: 'node-market',
        type: 'market_intelligence',
        confidence: 68,
        status: 'needs_work',
        sources: ['reddit', 'producthunt'],
        source_pills: [
          { label: 'Reddit', count: 312 },
          { label: 'Product Hunt', count: 89 },
        ],
        agent_notes: 'Market scan complete — $4.2B TAM in US independent restaurants',
        title: 'Market Intelligence',
        summary: 'Fragmented market with high operational pain — inventory waste costs $25B/yr',
        last_updated: minsAgo(38),
        active_agents: ['researcher_2'],
        overview:
          'The independent restaurant segment shows strong demand for operational automation. Owners spend 4+ hours daily on non-customer-facing tasks.',
        pain_points: [
          { label: 'Inventory waste and spoilage', percentage: 34 },
          { label: 'Staff scheduling conflicts', percentage: 28 },
          { label: 'Supplier price tracking', percentage: 22 },
          { label: 'Health code compliance', percentage: 16 },
        ],
      },
      {
        node_id: 'node-competitors',
        type: 'competitors',
        confidence: 61,
        status: 'needs_work',
        sources: ['exa', 'producthunt'],
        source_pills: [
          { label: 'Exa', count: 14 },
          { label: 'Product Hunt', count: 6 },
        ],
        agent_notes: '14 direct competitors mapped — gap in AI-native conversational UX',
        title: 'Competitors',
        summary: 'Marketoo, 7shifts, Toast — none offer conversational AI for ops',
        last_updated: minsAgo(30),
        active_agents: [],
      },
      lockedNode('node-revenue', 'revenue', 'Revenue Model', 'Unlocks when Audience + Market reach 70%'),
      lockedNode('node-product', 'product_vision', 'Product Vision', 'Unlocks when Audience + Market reach 70%'),
      lockedNode('node-tech', 'tech_stack', 'Tech Stack', 'Unlocks when Competitors + Core Idea reach 70%'),
      lockedNode('node-build', 'build', 'Build Node', 'Connect GitHub to unlock'),
      lockedNode('node-launch', 'launch', 'Launch Node', 'Unlocks after Build'),
      lockedNode('node-observe', 'observe', 'Observe Node', 'Connect PostHog to unlock'),
      lockedNode('node-growth', 'growth', 'Growth Node', 'Unlocks after Observe'),
    ],
  }
}

export function createFullDemoWorkspace(): Workspace {
  return createStage2Workspace()
}

export const MOCK_FEED_SEQUENCE: { delay: number; message: { text: string; type: 'info' | 'critique' | 'done'; node_id?: string; score?: number } }[] = [
  { delay: 500, message: { text: '[Orchestrator] Workspace created. Spawning research agents...', type: 'info' } },
  { delay: 1200, message: { text: '[Researcher R1] Running Reddit scan for pain points...', type: 'info', node_id: 'node-audience' } },
  { delay: 2000, message: { text: '[Researcher R2] Querying GummySearch for market signals...', type: 'info', node_id: 'node-market' } },
  { delay: 2800, message: { text: '[Critique: 63/100] Too broad — refining query to independent owners', type: 'critique', score: 63 } },
  { delay: 3600, message: { text: '[Researcher R1] Found 847 Reddit posts — analyzing sentiment...', type: 'info', node_id: 'node-audience' } },
  { delay: 4400, message: { text: '[Critique: 81/100] Committed — audience segment validated', type: 'critique', score: 81 } },
  { delay: 5200, message: { text: '[Researcher R2] Market scan complete — 4 pain points ranked', type: 'info', node_id: 'node-market' } },
  { delay: 6000, message: { text: '[Researcher R1] Competitor landscape mapped — 14 direct, 6 indirect', type: 'info', node_id: 'node-competitors' } },
  { delay: 6800, message: { text: '[Orchestrator] Stage 2 complete. Dialogue agent ready.', type: 'done' } },
]

export const MOCK_CHAT_MESSAGES = [
  {
    role: 'user' as const,
    text: 'What are the top pain points for restaurant owners?',
  },
  {
    role: 'agent' as const,
    agentName: 'Researcher 2',
    text: 'Based on 312 Reddit posts and 89 Product Hunt reviews, the top pain points are: inventory waste (34%), staff scheduling (28%), supplier tracking (22%), and health compliance (16%). Independent owners with 1-3 locations feel these most acutely.',
  },
]

export const MOCK_AWAY_NOTIFICATION =
  'While you were away: 2 new competitors found · Reddit sentiment shifted · Signup conversion dropped'

export const MOCK_EXPORT_FILES = [
  'README.md',
  'tech_stack.md',
  'product_vision.md',
  'market_analysis.md',
  'competitor_matrix.csv',
  'prd_draft.md',
]
