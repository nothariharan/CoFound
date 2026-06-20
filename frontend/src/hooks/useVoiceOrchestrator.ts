import { useCallback, useEffect } from 'react'
import type { ChatMessage, NodeType, UiAction } from '@/types'
import { apiUrl } from '@/lib/api'
import { useAgentActions } from '@/hooks/useAgentActions'
import { useWorkspace } from '@/hooks/useWorkspace'
import { useWorkspaceStore } from '@/store/workspaceStore'
import {
  hasWorkspaceWelcome,
  markWorkspaceWelcomed,
  startVoiceRecording,
  stopVoiceRecording,
} from '@/lib/voiceRecorder'

async function transcribeBlob(blob: Blob): Promise<string> {
  const form = new FormData()
  form.append('audio', blob, 'recording.webm')
  const res = await fetch(apiUrl('/api/voice/stt'), { method: 'POST', body: form })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || 'Speech-to-text failed')
  }
  const data = (await res.json()) as { transcript: string }
  return data.transcript.trim()
}

async function playTts(text: string): Promise<void> {
  const res = await fetch(apiUrl('/api/voice/tts'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) return
  const buffer = await res.arrayBuffer()
  const blob = new Blob([buffer], { type: 'audio/mpeg' })
  const url = URL.createObjectURL(blob)
  return new Promise((resolve, reject) => {
    const audio = new Audio(url)
    audio.onended = () => {
      URL.revokeObjectURL(url)
      resolve()
    }
    audio.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to play speech'))
    }
    void audio.play().catch(reject)
  })
}

export function useVoiceOrchestrator() {
  const {
    workspace,
    orchestratorMessages,
    voiceState,
    appendOrchestratorMessage,
    setOrchestratorMessages,
    setVoiceState,
    setHasChatted,
    setSelectedNodeId,
    setSettingsOpen,
    setExportOpen,
    setJournalOpen,
    setIntegrationDialogId,
  } = useWorkspaceStore()

  const { sendOrchestratorChat } = useAgentActions()
  const { fetchWorkspace } = useWorkspace()

  const startListening = useCallback(async () => {
    if (voiceState !== 'idle') return
    try {
      await startVoiceRecording()
      setVoiceState('listening')
    } catch {
      appendOrchestratorMessage({
        role: 'agent',
        agentName: 'System',
        text: 'Microphone access denied. Use text chat instead.',
      })
    }
  }, [voiceState, setVoiceState, appendOrchestratorMessage])

  const executeUiActions = useCallback(
    (actions: UiAction[]) => {
      for (const action of actions) {
        const payload = action.payload ?? {}
        switch (action.type) {
          case 'select_node': {
            const nodeType = payload.node_type as NodeType | undefined
            if (!nodeType || !workspace) break
            const node = workspace.nodes.find((item) => item.type === nodeType)
            if (node) setSelectedNodeId(node.node_id)
            break
          }
          case 'open_settings':
            setSettingsOpen(true)
            break
          case 'open_export':
            setExportOpen(true)
            break
          case 'open_journal':
            setJournalOpen(true)
            break
          case 'open_integrations':
            setIntegrationDialogId(payload.integration_id ?? 'github')
            break
          default:
            break
        }
      }
    },
    [
      workspace,
      setSelectedNodeId,
      setSettingsOpen,
      setExportOpen,
      setJournalOpen,
      setIntegrationDialogId,
    ],
  )

  const sendMessage = useCallback(
    async (text: string, options?: { speak?: boolean }) => {
      if (!workspace?.idea_id || !text.trim()) return

      const userMsg: ChatMessage = { role: 'user', text: text.trim() }
      appendOrchestratorMessage(userMsg)
      setHasChatted(true)
      setVoiceState('thinking')

      try {
        const result = await sendOrchestratorChat(workspace.idea_id, text.trim(), [
          ...orchestratorMessages,
          userMsg,
        ])
        const agentMsg: ChatMessage = {
          role: 'agent',
          agentName: 'Orchestrator',
          text: result.reply,
          actionsTaken: result.actions_taken,
        }
        appendOrchestratorMessage(agentMsg)
        if (result.ui_actions?.length) {
          executeUiActions(result.ui_actions)
        }
        if (result.actions_taken?.length) {
          await fetchWorkspace(workspace.idea_id)
        }

        const speakText = result.speaking_text || result.reply
        if (options?.speak !== false && speakText) {
          setVoiceState('speaking')
          try {
            await playTts(speakText)
          } catch {
            // tts optional — chat still works
          }
        }
      } catch (error) {
        appendOrchestratorMessage({
          role: 'agent',
          agentName: 'System',
          text: error instanceof Error ? error.message : 'Failed to reach the orchestrator.',
        })
      } finally {
        setVoiceState('idle')
      }
    },
    [
      workspace?.idea_id,
      orchestratorMessages,
      appendOrchestratorMessage,
      setHasChatted,
      setVoiceState,
      sendOrchestratorChat,
      executeUiActions,
      fetchWorkspace,
    ],
  )

  const stopListening = useCallback(async () => {
    if (voiceState !== 'listening') return

    setVoiceState('transcribing')
    const blob = await stopVoiceRecording()
    if (!blob) {
      setVoiceState('idle')
      return
    }

    try {
      const transcript = await transcribeBlob(blob)
      if (transcript) {
        await sendMessage(transcript, { speak: true })
      } else {
        setVoiceState('idle')
      }
    } catch (error) {
      appendOrchestratorMessage({
        role: 'agent',
        agentName: 'System',
        text: error instanceof Error ? error.message : 'Could not transcribe audio.',
      })
      setVoiceState('idle')
    }
  }, [voiceState, appendOrchestratorMessage, sendMessage, setVoiceState])

  const toggleListening = useCallback(async () => {
    if (voiceState === 'listening') {
      await stopListening()
      return
    }
    if (voiceState === 'idle') {
      await startListening()
    }
  }, [voiceState, startListening, stopListening])

  useEffect(() => {
    if (!workspace?.idea_id || hasWorkspaceWelcome(workspace.idea_id)) return
    if (orchestratorMessages.length > 0) {
      markWorkspaceWelcomed(workspace.idea_id)
      return
    }
    markWorkspaceWelcomed(workspace.idea_id)
    void sendOrchestratorChat(workspace.idea_id, 'Give me a brief welcome and current status.', [])
      .then((result) => {
        setOrchestratorMessages([
          {
            role: 'agent',
            agentName: 'Orchestrator',
            text: result.reply,
            actionsTaken: result.actions_taken,
          },
        ])
      })
      .catch(() => {
        setOrchestratorMessages([
          {
            role: 'agent',
            agentName: 'Orchestrator',
            text: 'Talk or type to ask for updates, start research, or manage your startup graph.',
          },
        ])
      })
  }, [workspace?.idea_id, orchestratorMessages.length, sendOrchestratorChat, setOrchestratorMessages])

  return {
    messages: orchestratorMessages,
    voiceState,
    toggleListening,
    sendMessage,
    executeUiActions,
  }
}
