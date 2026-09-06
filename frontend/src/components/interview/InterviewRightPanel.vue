<script setup lang="ts">
import { Lightbulb, Trash2 } from '@lucide/vue'
import type { Difficulty, InterviewMode, ResponseStyle } from '@/types/interview'

const mode = defineModel<InterviewMode>('mode', { default: 'practice' })
const responseStyle = defineModel<ResponseStyle>('responseStyle', { default: 'detailed' })
const difficulty = defineModel<Difficulty>('difficulty', { default: 'medium' })
const includeCode = defineModel<boolean>('includeCode', { default: true })
const followUps = defineModel<boolean>('followUps', { default: true })
const bestPractices = defineModel<boolean>('bestPractices', { default: true })

defineProps<{
  topicLabel: string
  roleLabel: string
}>()

defineEmits<{
  clear: []
}>()
</script>

<template>
  <aside class="flex h-full w-[320px] shrink-0 flex-col overflow-y-auto bg-white px-4 pb-4">
    <h2 class="text-sm font-bold text-slate-800">Chat Settings</h2>

    <section class="mt-4">
      <p class="text-xs font-semibold text-slate-700">Interview Mode</p>
      <div class="mt-2 grid grid-cols-2 gap-2">
        <button
          class="rounded-xl px-3 py-2 text-sm font-semibold"
          type="button"
          :class="mode === 'practice' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600'"
          @click="mode = 'practice'"
        >
          Practice
        </button>
        <button
          class="rounded-xl px-3 py-2 text-sm font-semibold"
          type="button"
          :class="mode === 'mock' ? 'bg-violet-600 text-white' : 'bg-slate-100 text-slate-600'"
          @click="mode = 'mock'"
        >
          Mock Interview
        </button>
      </div>
    </section>

    <label class="mt-4 block text-xs font-semibold text-slate-700">
      Response Style
      <select
        v-model="responseStyle"
        class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none focus:border-brand"
      >
        <option value="detailed">Detailed Explanation</option>
        <option value="concise">Concise</option>
        <option value="socratic">Socratic (hints first)</option>
      </select>
    </label>

    <label class="mt-4 block text-xs font-semibold text-slate-700">
      Difficulty Level
      <select
        v-model="difficulty"
        class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none focus:border-brand"
      >
        <option value="easy">Easy</option>
        <option value="medium">Medium</option>
        <option value="hard">Hard</option>
      </select>
    </label>

    <div class="mt-4 space-y-3">
      <label class="flex items-center justify-between gap-3 text-sm text-slate-700">
        Include code examples
        <input v-model="includeCode" class="h-4 w-8 accent-brand" type="checkbox" />
      </label>
      <label class="flex items-center justify-between gap-3 text-sm text-slate-700">
        Give follow-up questions
        <input v-model="followUps" class="h-4 w-8 accent-brand" type="checkbox" />
      </label>
      <label class="flex items-center justify-between gap-3 text-sm text-slate-700">
        Provide best practices
        <input v-model="bestPractices" class="h-4 w-8 accent-brand" type="checkbox" />
      </label>
    </div>

    <button
      class="mt-4 inline-flex items-center justify-center gap-2 rounded-xl border border-red-100 bg-red-50 px-3 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-100"
      type="button"
      @click="$emit('clear')"
    >
      <Trash2 class="h-4 w-4" />
      Clear Chat
    </button>

    <div class="mt-auto rounded-xl bg-violet-50 p-3">
      <p class="flex items-center gap-1.5 text-xs font-semibold text-violet-800">
        <Lightbulb class="h-3.5 w-3.5" />
        Pro Tip
      </p>
      <p class="mt-1 text-[12px] leading-relaxed text-violet-800/80">
        Pick a topic on the left, then ask for comparisons, code walkthroughs, or a mock question at your chosen difficulty.
      </p>
    </div>
  </aside>
</template>
