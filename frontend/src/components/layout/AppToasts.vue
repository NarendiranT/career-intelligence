<script setup lang="ts">
import { CircleAlert, CircleCheck, Info, X } from '@lucide/vue'
import { useToast, type ToastTone } from '@/composables/useToast'

const { toasts, dismissToast } = useToast()

function toneClass(tone: ToastTone): string {
  if (tone === 'error') return 'border-red-200 bg-red-50 text-red-700'
  if (tone === 'success') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  return 'border-blue-200 bg-blue-50 text-brand'
}

function iconFor(tone: ToastTone) {
  if (tone === 'error') return CircleAlert
  if (tone === 'success') return CircleCheck
  return Info
}
</script>

<template>
  <div
    class="pointer-events-none fixed inset-x-0 top-4 z-[100] flex flex-col items-center gap-2 px-4"
    aria-live="polite"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="pointer-events-auto flex w-full max-w-lg items-start gap-3 rounded-xl border px-4 py-3 text-sm shadow-[0_12px_32px_rgba(15,23,42,0.12)]"
      :class="toneClass(toast.tone)"
      :role="toast.tone === 'error' ? 'alert' : 'status'"
    >
      <component :is="iconFor(toast.tone)" class="mt-0.5 h-4 w-4 shrink-0" />
      <p class="min-w-0 flex-1 font-medium leading-snug">{{ toast.message }}</p>
      <button
        class="rounded-md p-0.5 opacity-70 hover:opacity-100"
        type="button"
        aria-label="Dismiss notification"
        @click="dismissToast(toast.id)"
      >
        <X class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
