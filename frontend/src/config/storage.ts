export const WORKSPACE_KEY = 'cofounder_workspace_id'

export function getSavedWorkspaceId(): string | null {
  try {
    return localStorage.getItem(WORKSPACE_KEY)
  } catch {
    return null
  }
}

export function clearSavedWorkspaceId() {
  try {
    localStorage.removeItem(WORKSPACE_KEY)
  } catch {
    // ignore
  }
}

export function onboardingKey(ideaId: string) {
  return `cofounder_onboarding_${ideaId}`
}

export function getOnboardingDismissed(ideaId: string): boolean {
  try {
    return localStorage.getItem(onboardingKey(ideaId)) === 'dismissed'
  } catch {
    return false
  }
}

export function setOnboardingDismissed(ideaId: string) {
  try {
    localStorage.setItem(onboardingKey(ideaId), 'dismissed')
  } catch {
    // ignore
  }
}
