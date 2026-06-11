import type { NodeStatus, NodeType } from '@/types'

export const nodeTypeColors: Record<NodeType, string> = {
  core_idea: 'var(--node-core-idea)',
  audience: 'var(--node-audience)',
  market_intelligence: 'var(--node-market-intelligence)',
  competitors: 'var(--node-competitors)',
  revenue: 'var(--node-revenue)',
  product_vision: 'var(--node-product-vision)',
  tech_stack: 'var(--node-tech-stack)',
  build: 'var(--node-build)',
  launch: 'var(--node-launch)',
  observe: 'var(--node-observe)',
  growth: 'var(--node-growth)',
  custom_research: '#8b5cf6',
}

export const statusColors: Record<NodeStatus, string> = {
  validated: 'var(--status-validated)',
  needs_work: 'var(--status-needs-work)',
  blocking: 'var(--status-blocking)',
  locked: 'var(--status-locked)',
}

export const statusLabels: Record<NodeStatus, string> = {
  validated: 'Validated',
  needs_work: 'Needs Work',
  blocking: 'Blocking',
  locked: 'Locked',
}

export const statusBadgeVariant: Record<NodeStatus, 'success' | 'warning' | 'destructive' | 'secondary'> = {
  validated: 'success',
  needs_work: 'warning',
  blocking: 'destructive',
  locked: 'secondary',
}

export function getStatusColor(status: NodeStatus): string {
  return statusColors[status]
}

export function getNodeTypeColor(type: NodeType): string {
  return nodeTypeColors[type]
}

const statusTextClasses: Record<NodeStatus, string> = {
  validated: 'text-status-validated',
  needs_work: 'text-status-needs-work',
  blocking: 'text-status-blocking',
  locked: 'text-status-locked',
}

export function getStatusTextClass(status: NodeStatus): string {
  return statusTextClasses[status]
}

export function getRingColor(confidence: number, status: NodeStatus): string {
  if (status === 'locked') return statusColors.locked
  if (confidence >= 80) return statusColors.validated
  if (confidence >= 50) return statusColors.needs_work
  return statusColors.blocking
}
