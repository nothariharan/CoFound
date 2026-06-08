import type { IntegrationInfo } from '@/types'

export const INTEGRATION_CATALOG: IntegrationInfo[] = [
  {
    id: 'github',
    label: 'GitHub',
    connected: false,
    status: 'available',
    description: 'Connect your repository so agents can track commits and unlock the Build node.',
    unlocks: 'Build node',
  },
  {
    id: 'posthog',
    label: 'PostHog',
    connected: false,
    status: 'available',
    description: 'Connect analytics to monitor funnel drops and unlock the Observe node.',
    unlocks: 'Observe node',
  },
  {
    id: 'reddit',
    label: 'Reddit',
    connected: true,
    status: 'connected',
    description: 'Reddit research is always on — agents scan communities for pain points automatically.',
  },
  {
    id: 'gmail',
    label: 'Gmail',
    connected: false,
    status: 'coming_soon',
    description: 'Email outreach and customer discovery — coming soon.',
  },
  {
    id: 'slack',
    label: 'Slack',
    connected: false,
    status: 'coming_soon',
    description: 'Team notifications and agent alerts — coming soon.',
  },
  {
    id: 'gummysearch',
    label: 'GummySearch',
    connected: false,
    status: 'coming_soon',
    description: 'Reddit audience research via GummySearch — coming soon.',
  },
]

export function mergeIntegrationStatus(
  catalog: IntegrationInfo[],
  status: { github: boolean; posthog: boolean; reddit: boolean; gummysearch: boolean },
): IntegrationInfo[] {
  return catalog.map((item) => {
    if (item.status === 'coming_soon') return item
    if (item.id === 'github') {
      return { ...item, connected: status.github, status: status.github ? 'connected' : 'available' }
    }
    if (item.id === 'posthog') {
      return { ...item, connected: status.posthog, status: status.posthog ? 'connected' : 'available' }
    }
    if (item.id === 'reddit') {
      return { ...item, connected: status.reddit, status: 'connected' }
    }
    if (item.id === 'gummysearch') {
      return { ...item, connected: status.gummysearch, status: status.gummysearch ? 'connected' : 'coming_soon' }
    }
    return item
  })
}
