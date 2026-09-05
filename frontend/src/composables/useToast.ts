import { ref } from 'vue'

export type ToastTone = 'error' | 'success' | 'info'

export type Toast = {
  id: number
  message: string
  tone: ToastTone
}

const toasts = ref<Toast[]>([])
let nextId = 1
const timers = new Map<number, number>()

export function dismissToast(id: number): void {
  const timer = timers.get(id)
  if (timer) {
    window.clearTimeout(timer)
    timers.delete(id)
  }
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

export function showToast(message: string, tone: ToastTone = 'info', durationMs = 6000): void {
  const text = message.trim()
  if (!text) return
  const id = nextId++
  toasts.value = [...toasts.value, { id, message: text, tone }]
  if (durationMs > 0) {
    const timer = window.setTimeout(() => dismissToast(id), durationMs)
    timers.set(id, timer)
  }
}

export function useToast() {
  return { toasts, showToast, dismissToast }
}
