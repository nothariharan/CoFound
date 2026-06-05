import type { NodeStatus } from '@/types'

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

export function getRingColor(confidence: number, status: NodeStatus): string {
  if (status === 'locked') return statusColors.locked
  if (confidence >= 80) return statusColors.validated
  if (confidence >= 50) return statusColors.needs_work
  return statusColors.blocking
}
