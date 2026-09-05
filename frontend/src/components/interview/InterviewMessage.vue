<script setup lang="ts">
import { computed } from 'vue'
import { Copy, Sparkles, ThumbsDown, ThumbsUp } from '@lucide/vue'
import { showToast } from '@/composables/useToast'
import { useAuth } from '@/composables/useAuth'
import type { InterviewMessage } from '@/types/interview'

const props = defineProps<{
  message: InterviewMessage
}>()

const { user } = useAuth()

const initials = computed(() => {
  const name = user.value?.full_name?.trim()
  if (name) {
    const parts = name.split(/\s+/).filter(Boolean)
    const letters = (parts[0]?.[0] ?? '') + (parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : '')
    return letters.toUpperCase() || 'CI'
  }
  const email = user.value?.email ?? ''
  return (email[0] ?? 'C').toUpperCase()
})

async function copyText(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value)
    showToast('Copied to clipboard', 'success')
  } catch {
    showToast('Could not copy', 'error')
  }
}

function copyMessage(): void {
  const parts = [props.message.text]
  if (props.message.code?.content) parts.push(props.message.code.content)
  void copyText(parts.join('\n\n'))
}
</script>

<template>
  <article v-if="message.role === 'user'" class="flex justify-end gap-3">
    <div class="max-w-[85%] rounded-2xl rounded-br-md bg-brand px-4 py-3 text-white">
      <p class="text-sm leading-relaxed">{{ message.text }}</p>
    </div>
    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-white">
      {{ initials }}
    </span>
  </article>

  <article v-else class="flex gap-3">
    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-600 text-white">
      <Sparkles class="h-4 w-4" />
    </span>
    <div class="max-w-[92%] min-w-0 flex-1 rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
      <p class="text-sm leading-relaxed whitespace-pre-wrap text-slate-800">{{ message.text }}</p>

      <div v-if="message.table" class="mt-4 overflow-x-auto rounded-xl border border-slate-200">
        <table class="w-full min-w-[420px] text-left text-sm">
          <thead class="bg-slate-50 text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
            <tr>
              <th v-for="header in message.table.headers" :key="header" class="px-3 py-2">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in message.table.rows" :key="index" class="border-t border-slate-100">
              <td v-for="(cell, cellIndex) in row" :key="cellIndex" class="px-3 py-2 text-slate-700" :class="cellIndex === 0 ? 'font-medium text-slate-800' : ''">
                {{ cell }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="message.code" class="relative mt-4 overflow-hidden rounded-xl bg-slate-900">
        <div class="flex items-center justify-between border-b border-white/10 px-3 py-1.5">
          <span class="text-[11px] font-medium tracking-wide text-slate-400 uppercase">{{ message.code.language }}</span>
          <button
            class="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-white/10"
            type="button"
            @click="copyText(message.code!.content)"
          >
            <Copy class="h-3 w-3" />
            Copy
          </button>
        </div>
        <pre class="overflow-x-auto p-3 text-[12px] leading-relaxed text-slate-100"><code>{{ message.code.content }}</code></pre>
      </div>

      <div class="mt-3 flex items-center justify-between">
        <div class="flex gap-2 text-slate-400">
          <button class="rounded-md p-1 hover:bg-slate-50 hover:text-slate-700" type="button" aria-label="Good response">
            <ThumbsUp class="h-3.5 w-3.5" />
          </button>
          <button class="rounded-md p-1 hover:bg-slate-50 hover:text-slate-700" type="button" aria-label="Bad response">
            <ThumbsDown class="h-3.5 w-3.5" />
          </button>
          <button class="rounded-md p-1 hover:bg-slate-50 hover:text-slate-700" type="button" aria-label="Copy response" @click="copyMessage">
            <Copy class="h-3.5 w-3.5" />
          </button>
        </div>
        <p class="text-[11px] text-slate-400">{{ message.time }}</p>
      </div>
    </div>
  </article>
</template>
