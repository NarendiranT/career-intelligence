<script setup lang="ts">
import { Check, Copy, Sparkles, ThumbsDown, ThumbsUp, TriangleAlert } from '@lucide/vue'
import type { ChatMessage } from '@/types/chat'

defineProps<{
  message: ChatMessage
}>()
</script>

<template>
  <article v-if="message.role === 'user'" class="flex gap-3">
    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-white">
      JD
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
        <button type="button" aria-label="Copy"><Copy class="h-3.5 w-3.5" /></button>
        <button type="button" aria-label="Good response"><ThumbsUp class="h-3.5 w-3.5" /></button>
        <button type="button" aria-label="Bad response"><ThumbsDown class="h-3.5 w-3.5" /></button>
      </div>
      <p class="text-sm leading-relaxed text-slate-800">{{ message.text }}</p>
      <div v-if="message.strengths?.length" class="mt-3">
        <p class="text-sm font-semibold text-slate-800">Key Strengths</p>
        <ul class="mt-1.5 space-y-1">
          <li v-for="item in message.strengths" :key="item" class="flex items-start gap-2 text-sm text-slate-700">
            <Check class="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
            {{ item }}
          </li>
        </ul>
      </div>
      <div v-if="message.gaps?.length" class="mt-3">
        <p class="text-sm font-semibold text-slate-800">Potential Gaps</p>
        <ul class="mt-1.5 space-y-1">
          <li v-for="item in message.gaps" :key="item" class="flex items-start gap-2 text-sm text-slate-700">
            <TriangleAlert class="mt-0.5 h-4 w-4 shrink-0 text-orange-500" />
            {{ item }}
          </li>
        </ul>
      </div>
      <div v-if="message.sources?.length" class="mt-3 flex flex-wrap items-center gap-2">
        <span class="text-[11px] font-medium text-slate-400">Sources</span>
        <span
          v-for="source in message.sources"
          :key="source.id"
          class="rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[11px] text-slate-600"
        >
          {{ source.label }}
        </span>
      </div>
      <p class="mt-2 text-[11px] text-slate-400">{{ message.time }}</p>
    </div>
  </article>
</template>
