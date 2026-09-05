<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { X } from '@lucide/vue'

const props = defineProps<{
  open: boolean
  title: string
  src: string
}>()

const emit = defineEmits<{ close: [] }>()

function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) emit('close')
}

watch(
  () => props.open,
  (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-slate-900/50 p-4"
      role="presentation"
      @click.self="emit('close')"
    >
      <div
        class="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-[0_24px_64px_rgba(15,23,42,0.28)]"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <header class="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-3">
          <h2 class="text-sm font-semibold text-slate-800">{{ title }}</h2>
          <div class="flex items-center gap-2">
            <a
              class="rounded-lg px-3 py-1.5 text-sm font-medium text-brand hover:bg-brand/5"
              :href="src"
              target="_blank"
              rel="noopener"
            >
              Open PDF
            </a>
            <button
              class="rounded-lg p-1.5 text-slate-400 hover:bg-slate-50 hover:text-slate-700"
              type="button"
              aria-label="Close sample"
              @click="emit('close')"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
        </header>
        <iframe class="min-h-[70vh] w-full flex-1 bg-slate-100" :src="src" :title="title" />
      </div>
    </div>
  </Teleport>
</template>
