type VoiceRecorderListener = (listening: boolean) => void

let mediaRecorder: MediaRecorder | null = null
let stream: MediaStream | null = null
let chunks: Blob[] = []
const listeners = new Set<VoiceRecorderListener>()

function notify(listening: boolean) {
  listeners.forEach((listener) => listener(listening))
}

export function subscribeVoiceRecorder(listener: VoiceRecorderListener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export async function startVoiceRecording(): Promise<void> {
  if (mediaRecorder?.state === 'recording') return
  stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  mediaRecorder = new MediaRecorder(stream)
  chunks = []
  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data)
  }
  mediaRecorder.start()
  notify(true)
}

export async function stopVoiceRecording(): Promise<Blob | null> {
  const recorder = mediaRecorder
  if (!recorder || recorder.state === 'inactive') {
    notify(false)
    return null
  }

  const blob = await new Promise<Blob>((resolve) => {
    recorder.onstop = () => {
      resolve(new Blob(chunks, { type: 'audio/webm' }))
    }
    recorder.stop()
  })

  stream?.getTracks().forEach((track) => track.stop())
  stream = null
  mediaRecorder = null
  chunks = []
  notify(false)
  return blob.size < 100 ? null : blob
}

export function isRecording(): boolean {
  return mediaRecorder?.state === 'recording'
}

const welcomedWorkspaces = new Set<string>()

export function markWorkspaceWelcomed(id: string) {
  welcomedWorkspaces.add(id)
}

export function hasWorkspaceWelcome(id: string) {
  return welcomedWorkspaces.has(id)
}

export function resetVoiceSession() {
  welcomedWorkspaces.clear()
}
