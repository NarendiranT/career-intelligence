<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, Copy, FileText, Mic, Sparkles, ThumbsDown, ThumbsUp, TriangleAlert } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'
import { showToast } from '@/composables/useToast'
import type { ChatFeedback, ChatMessage, ChatSource } from '@/types/chat'
import type { ApiDocument } from '@/types/document'
import { fileBadge } from '@/types/upload'
import { sourceFileName, stripInlineCitations } from '@/utils/chatSources'

const FEEDBACK_KEY = 'ci.chatFeedback'

const props = defineProps<{
  message: ChatMessage
  documents?: ApiDocument[]
  resumeId?: string
  jobIds?: string[]
  preparing?: boolean
}>()

const emit = defineEmits<{
  previewSource: [source: ChatSource]
  prepareInterview: [message: ChatMessage]
}>()

const { initials } = useAuth()
const copied = ref(false)

function readFeedback(): ChatFeedback | null {
  try {
    const raw = localStorage.getItem(FEEDBACK_KEY)
    if (!raw) return null
    const map = JSON.parse(raw) as Record<string, ChatFeedback>
    return map[props.message.id] ?? null
  } catch {
    return null
  }
}

const feedback = ref<ChatFeedback | null>(readFeedback())

const sourceCtx = () => ({
  documents: props.documents ?? [],
  resumeId: props.resumeId,
  jobIds: props.jobIds,
})

function sourceName(source: ChatSource): string {
  return sourceFileName(source, sourceCtx())
}

function displayText(value: string): string {
  return stripInlineCitations(value)
}

const canPrepareInterview = computed(
  () =>
    props.message.role === 'assistant' &&
    !props.message.pending &&
    Boolean(displayText(props.message.text)) &&
    props.message.validated === true,
)

async function copyMessage(): Promise<void> {
  const text = displayText(props.message.text)
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    showToast('Copied to clipboard', 'success', 2000)
    window.setTimeout(() => {
      copied.value = false
    }, 1500)
  } catch {
    showToast('Could not copy that reply', 'error')
  }
}

function setFeedback(value: ChatFeedback): void {
  feedback.value = feedback.value === value ? null : value
  try {
    const raw = localStorage.getItem(FEEDBACK_KEY)
    const map = raw ? (JSON.parse(raw) as Record<string, ChatFeedback | null>) : {}
    if (feedback.value) map[props.message.id] = feedback.value
    else delete map[props.message.id]
    localStorage.setItem(FEEDBACK_KEY, JSON.stringify(map))
  } catch {
    /* ignore quota / private mode */
  }
}
</script>

<template>
  <article v-if="message.role === 'user'" class="flex gap-3">
    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-white">
      {{ initials }}
    </span>
    <div class="max-w-[85%] rounded-2xl rounded-tl-md bg-[#e8f1ff] px-4 py-3">
      <p class="text-sm leading-relaxed text-slate-800">{{ message.text }}</p>
      <p class="mt-2 text-[11px] text-slate-400">{{ message.time }}</p>
    </div>
  </article>

  <article v-else class="flex gap-3">
    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-600 text-white">
      <Sparkles class="h-4 w-4" />
    </span>
    <div class="max-w-[90%] flex-1 rounded-2xl rounded-tl-md bg-[#f4f1ff] px-4 py-3">
      <div class="mb-2 flex justify-end gap-2 text-slate-400">
        <button
          class="rounded-md p-0.5 hover:text-slate-700"
          type="button"
          aria-label="Copy"
          :disabled="!message.text.trim()"
          @click="copyMessage"
        >
          <Check v-if="copied" class="h-3.5 w-3.5 text-emerald-600" />
          <Copy v-else class="h-3.5 w-3.5" />
        </button>
        <button
          class="rounded-md p-0.5 hover:text-slate-700"
          type="button"
          aria-label="Good response"
          :class="feedback === 'up' ? 'text-brand' : ''"
          :aria-pressed="feedback === 'up'"
          @click="setFeedback('up')"
        >
          <ThumbsUp class="h-3.5 w-3.5" />
        </button>
        <button
          class="rounded-md p-0.5 hover:text-slate-700"
          type="button"
          aria-label="Bad response"
          :class="feedback === 'down' ? 'text-orange-500' : ''"
          :aria-pressed="feedback === 'down'"
          @click="setFeedback('down')"
        >
          <ThumbsDown class="h-3.5 w-3.5" />
        </button>
      </div>
      <p v-if="message.pending && !message.text" class="text-sm text-slate-500">Thinking…</p>
      <p v-else class="text-sm leading-relaxed text-slate-800">
        {{ displayText(message.text) }}<span v-if="message.pending" class="animate-pulse">▍</span>
      </p>
      <div v-if="message.strengths?.length" class="mt-3">
        <p class="text-sm font-semibold text-slate-800">Key Strengths</p>
        <ul class="mt-1.5 space-y-1">
          <li v-for="item in message.strengths" :key="item" class="flex items-start gap-2 text-sm text-slate-700">
            <Check class="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
            {{ displayText(item) }}
          </li>
        </ul>
      </div>
      <div v-if="message.gaps?.length" class="mt-3">
        <p class="text-sm font-semibold text-slate-800">Potential Gaps</p>
        <ul class="mt-1.5 space-y-1">
          <li v-for="item in message.gaps" :key="item" class="flex items-start gap-2 text-sm text-slate-700">
            <TriangleAlert class="mt-0.5 h-4 w-4 shrink-0 text-orange-500" />
            {{ displayText(item) }}
          </li>
        </ul>
      </div>
      <div v-if="message.sources?.length" class="mt-3 flex flex-wrap items-center gap-2">
        <span class="text-[11px] font-medium text-slate-400">Sources</span>
        <button
          v-for="source in message.sources"
          :key="source.id || source.label"
          class="inline-flex max-w-full items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[11px] text-slate-600 hover:border-brand hover:text-brand"
          type="button"
          :title="sourceName(source)"
          @click="emit('previewSource', source)"
        >
          <FileText class="h-3 w-3 shrink-0 text-slate-400" />
          <span class="truncate">{{ sourceName(source) }}</span>
          <span class="text-[9px] font-semibold tracking-wide text-slate-400">{{ fileBadge(sourceName(source)) }}</span>
        </button>
      </div>
      <p class="mt-2 text-[11px] text-slate-400">
        {{ message.time }}
        <span v-if="message.usage && message.usage.tokens > 0" class="ml-2">
          {{ message.usage.tokens.toLocaleString() }} tokens
          ({{ message.usage.prompt_tokens.toLocaleString() }} prompt /
          {{ message.usage.completion_tokens.toLocaleString() }} completion)
        </span>
      </p>
      <button
        v-if="canPrepareInterview"
        class="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-violet-200 bg-white px-2.5 py-1.5 text-[12px] font-semibold text-violet-700 hover:bg-violet-50 disabled:opacity-50"
        type="button"
        :disabled="preparing"
        @click="emit('prepareInterview', message)"
      >
        <Mic class="h-3.5 w-3.5" />
        {{ preparing ? 'Creating topics…' : message.topics?.length ? 'Continue interview' : 'Prepare for interview' }}
      </button>
    </div>
  </article>
</template>
