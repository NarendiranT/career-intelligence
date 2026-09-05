<script setup lang="ts">
import { Globe, Paperclip, Send } from '@lucide/vue'

const draft = defineModel<string>('draft', { default: '' })
const modelValue = defineModel<string>('model', { default: 'deep-research' })

const models = [
  { id: 'deep-research', label: 'Deep Research' },
  { id: 'gpt-4o', label: 'GPT-4o' },
  { id: 'claude-3.5', label: 'Claude 3.5' },
  { id: 'gemini-pro', label: 'Gemini Pro' },
]

defineEmits<{
  send: []
}>()
</script>

<template>
  <form class="border-t border-slate-100 bg-white p-4" @submit.prevent="$emit('send')">
    <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <textarea
        v-model="draft"
        class="h-16 w-full resize-none bg-transparent px-1 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400"
        placeholder="Ask a question about your resume or job descriptions..."
        @keydown.enter.exact.prevent="$emit('send')"
      />
      <div class="flex items-center justify-between gap-3 pb-1">
        <div class="flex items-center gap-1 text-slate-400">
          <button class="rounded-lg p-2 hover:bg-slate-50" type="button" aria-label="Attach">
            <Paperclip class="h-4 w-4" />
          </button>
          <button class="rounded-lg p-2 hover:bg-slate-50" type="button" aria-label="Web search">
            <Globe class="h-4 w-4" />
          </button>
          <select
            v-model="modelValue"
            class="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 outline-none"
          >
            <option v-for="item in models" :key="item.id" :value="item.id">{{ item.label }}</option>
          </select>
        </div>
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full bg-brand text-white hover:bg-brand-dark disabled:opacity-40"
          type="submit"
          :disabled="!draft.trim()"
          aria-label="Send"
        >
          <Send class="h-4 w-4" />
        </button>
      </div>
    </div>
  </form>
</template>
