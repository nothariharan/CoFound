import type { NodeStatus } from '../types'

export const statusColors: Record<NodeStatus, string> = {
  validated: '#16a34a',
  needs_work: '#ca8a04',
  blocking: '#dc2626',
  locked: '#a3a3a3',
}

export const statusLabels: Record<NodeStatus, string> = {
  validated: 'Validated',
  needs_work: 'Needs Work',
  blocking: 'Blocking',
  locked: 'Locked',
}

export function getStatusColor(status: NodeStatus): string {
  return statusColors[status]
}

export function getRingColor(confidence: number, status: NodeStatus): string {
  if (status === 'locked') return statusColors.locked
  if (confidence >= 80) return statusColors.validated
  if (confidence >= 50) return statusColors.needs_work
  return statusColors.blocking
}
