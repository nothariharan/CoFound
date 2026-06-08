import { useCallback } from 'react'
import { WORKSPACE_KEY } from '@/config/storage'
import { stopDemoSequence } from '@/mock/demoEngine'
import { useWorkspaceStore } from '@/store/workspaceStore'

export function useGoHome() {
  const resetToHome = useWorkspaceStore((s) => s.resetToHome)
  const isDemo = useWorkspaceStore((s) => s.mode === 'demo')

  return useCallback(() => {
    if (isDemo) stopDemoSequence()
    localStorage.removeItem(WORKSPACE_KEY)
    resetToHome()
  }, [resetToHome, isDemo])
}
