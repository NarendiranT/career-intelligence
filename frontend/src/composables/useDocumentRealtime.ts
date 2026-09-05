import { onMounted, onUnmounted } from 'vue'
import { readToken } from '@/api/token'
import type { ApiDocument } from '@/types/document'

export type DocumentRealtimeEvent =
  | { type: 'document.status'; document: ApiDocument }
  | { type: 'document.deleted'; document_id: string }

type Listener = (event: DocumentRealtimeEvent) => void

const listeners = new Set<Listener>()
let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let attempts = 0
let wantOpen = false
let subscriberCount = 0

function wsUrl(token: string): string {
  const raw = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
  let proto: string
  let host: string
  if (raw) {
    const url = new URL(raw)
    proto = url.protocol === 'https:' ? 'wss:' : 'ws:'
    host = url.host
  } else {
    proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    host = window.location.host
  }
  return `${proto}//${host}/v1/ws/documents?token=${encodeURIComponent(token)}`
}

function notify(event: DocumentRealtimeEvent): void {
  for (const listener of listeners) listener(event)
}

function connect(): void {
  if (!wantOpen || socket) return
  const token = readToken()
  if (!token) return
  const ws = new WebSocket(wsUrl(token))
  socket = ws
  ws.onopen = () => {
    attempts = 0
  }
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as DocumentRealtimeEvent
      if (data?.type === 'document.status' && data.document?.id) {
        notify(data)
      }
      if (data?.type === 'document.deleted' && data.document_id) {
        notify(data)
      }
    } catch {
      /* ignore malformed frames */
    }
  }
  ws.onerror = () => {
    ws.close()
  }
  ws.onclose = () => {
    if (socket === ws) socket = null
    if (wantOpen) scheduleReconnect()
  }
}

function scheduleReconnect(): void {
  if (reconnectTimer != null) return
  const delay = Math.min(10_000, 500 * 2 ** attempts)
  attempts += 1
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    connect()
  }, delay)
}

function start(): void {
  wantOpen = true
  connect()
}

function stop(): void {
  wantOpen = false
  attempts = 0
  if (reconnectTimer != null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  socket?.close()
  socket = null
}

export function applyDocumentUpdate(list: ApiDocument[], doc: ApiDocument): ApiDocument[] {
  const index = list.findIndex((row) => row.id === doc.id)
  if (index === -1) {
    return [doc, ...list]
  }
  const next = list.slice()
  next[index] = { ...next[index], ...doc }
  return next
}

export function removeDocument(list: ApiDocument[], documentId: string): ApiDocument[] {
  return list.filter((row) => row.id !== documentId)
}

export function useDocumentRealtime(onEvent: Listener): void {
  onMounted(() => {
    listeners.add(onEvent)
    subscriberCount += 1
    if (subscriberCount === 1) start()
  })
  onUnmounted(() => {
    listeners.delete(onEvent)
    subscriberCount -= 1
    if (subscriberCount <= 0) {
      subscriberCount = 0
      stop()
    }
  })
}
