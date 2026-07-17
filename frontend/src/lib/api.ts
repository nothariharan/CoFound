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
    if (controller.signal.aborted) {
      throw new ApiError('The server took too long to respond. Please try again.')
    }
    throw new ApiError('Unable to connect to the server. Please try again in a moment.')
  } finally {
    window.clearTimeout(timeout)
    signal?.removeEventListener('abort', abort)
  }
}

export async function warmApi(signal?: AbortSignal): Promise<boolean> {
  try {
    await apiFetch('/health', { signal, timeoutMs: 45_000 })
    return true
  } catch {
    return false
  }
}

async function responseMessage(response: Response): Promise<string> {
  try {
    const body = (await response.clone().json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    // Fall through to plain text.
  }
  const text = await response.text().catch(() => '')
  return text || `Request failed (${response.status})`
}
