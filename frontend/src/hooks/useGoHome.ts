import { useCallback } from 'react'
import { WORKSPACE_KEY } from '@/config/storage'
import { useWorkspaceStore } from '@/store/workspaceStore'

export function useGoHome() {
  const resetToHome = useWorkspaceStore((s) => s.resetToHome)

  return useCallback(() => {
    localStorage.removeItem(WORKSPACE_KEY)
    resetToHome()
  }, [resetToHome])
}
