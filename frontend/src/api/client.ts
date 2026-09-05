import { showToast } from '@/composables/useToast'
import { clearToken, readToken } from './token'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type Json = Record<string, unknown> | unknown[] | string | number | boolean | null

let onUnauthorized: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL ?? ""
  return raw.replace(/\/$/, "")
}

function parseDetail(body: unknown): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg: unknown }).msg)
          }
          return String(item)
        })
        .join(' ')
    }
  }
  return 'Request failed'
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { json?: Json; skipAuth?: boolean; timeoutMs?: number } = {},
): Promise<T> {
  const { json, skipAuth, headers: initHeaders, timeoutMs = 15_000, signal: initSignal, ...init } =
    options
  const headers = new Headers(initHeaders)
  if (json !== undefined) {
    headers.set('Content-Type', 'application/json')
  }
  const token = skipAuth ? null : readToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers,
    body: json !== undefined ? JSON.stringify(json) : init.body,
    signal: initSignal ?? (timeoutMs > 0 ? AbortSignal.timeout(timeoutMs) : undefined),
  })

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  let body: unknown = null
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = text
    }
  }

  if (!response.ok) {
    if (response.status === 401 && token && !skipAuth) {
      clearToken()
      onUnauthorized?.()
    }
    const detail = parseDetail(body)
    if (response.status >= 500) {
      const message =
        detail === 'Request failed'
          ? 'Something went wrong on our side. Please try again.'
          : detail
      showToast(message, 'error')
    }
    throw new ApiError(detail, response.status)
  }

  return body as T
}
