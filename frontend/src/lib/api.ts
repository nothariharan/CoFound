const PRODUCTION_API = 'https://cofound-tshh.onrender.com'
const configuredBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
const API_BASE = (configuredBase || (import.meta.env.PROD ? PRODUCTION_API : '')).replace(/\/$/, '')

export class ApiError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function apiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${normalized}`
}

interface ApiFetchOptions extends RequestInit {
  timeoutMs?: number
}

export async function apiFetch(path: string, options: ApiFetchOptions = {}): Promise<Response> {
  const { timeoutMs = 60_000, signal, ...requestOptions } = options
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })

  try {
    const response = await fetch(apiUrl(path), { ...requestOptions, signal: controller.signal })
    if (!response.ok) {
      throw new ApiError(await responseMessage(response), response.status)
    }
    return response
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (signal?.aborted) {
      throw new ApiError('Request cancelled.', 499)
    }
    if (controller.signal.aborted) {
      throw new ApiError('The server took too long to respond. Please try again.', 408)
    }
    throw new ApiError('Unable to connect to the server. Please try again in a moment.')
  } finally {
    window.clearTimeout(timeout)
    signal?.removeEventListener('abort', abort)
  }
}

/** wake the free-tier api — retries through cold starts without treating remount aborts as downtime */
export async function warmApi(signal?: AbortSignal): Promise<boolean> {
  const attempts = 4
  for (let i = 0; i < attempts; i++) {
    if (signal?.aborted) return false
    try {
      await apiFetch('/health', { signal, timeoutMs: 90_000 })
      return true
    } catch (error) {
      if (signal?.aborted) return false
      const status = error instanceof ApiError ? error.status : undefined
      // cancelled by unmount / strict mode — not a real outage
      if (status === 499) return false
      // wait then retry; free render cold starts often need a second hit
      await sleep(2_500 + i * 2_000, signal)
    }
  }
  return false
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    if (signal?.aborted) {
      resolve()
      return
    }
    const timer = window.setTimeout(resolve, ms)
    signal?.addEventListener(
      'abort',
      () => {
        window.clearTimeout(timer)
        resolve()
      },
      { once: true },
    )
  })
}

async function responseMessage(response: Response): Promise<string> {
  try {
    const body = (await response.clone().json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    // fall through to plain text
  }
  const text = await response.text().catch(() => '')
  return text || `Request failed (${response.status})`
}
