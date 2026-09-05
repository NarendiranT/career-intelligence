import { onMounted, onUnmounted, ref } from 'vue'
import { readToken } from '@/api/token'
import type { ChatAskPayload, ChatSocketEvent } from '@/types/chat'

type Listener = (event: ChatSocketEvent) => void

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
  return `${proto}//${host}/v1/ws/chat?token=${encodeURIComponent(token)}`
}

export function useChatRealtime(onEvent: Listener) {
  const connected = ref(false)
  let socket: WebSocket | null = null
  let reconnectTimer: number | null = null
  let attempts = 0
  let wantOpen = false

  function connect(): void {
    if (!wantOpen || socket) return
    const token = readToken()
    if (!token) return
    const ws = new WebSocket(wsUrl(token))
    socket = ws
    ws.onopen = () => {
      attempts = 0
      connected.value = true
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ChatSocketEvent
        if (data?.type) onEvent(data)
      } catch {
        /* ignore malformed frames */
      }
    }
    ws.onerror = () => {
      ws.close()
    }
    ws.onclose = () => {
      connected.value = false
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

  function sendAsk(payload: ChatAskPayload): boolean {
    if (!socket || socket.readyState !== WebSocket.OPEN) return false
    socket.send(JSON.stringify({ type: 'chat.ask', ...payload }))
    return true
  }

  onMounted(() => {
    wantOpen = true
    connect()
  })

  onUnmounted(() => {
    wantOpen = false
    attempts = 0
    if (reconnectTimer != null) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    socket?.close()
    socket = null
    connected.value = false
  })

  return { connected, sendAsk }
}
