<script setup lang="ts">
import { ref } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatRightPanel from '@/components/chat/ChatRightPanel.vue'
import type { ChatMessage as ChatMessageType } from '@/types/chat'

const tab = ref<'documents' | 'settings'>('documents')
const selectedResumeId = ref('resume-1')
const selectedJobIds = ref(['job-1', 'job-2'])
const temperature = ref(0.7)
const topP = ref(1)
const maxTokens = ref(1024)
const model = ref('deep-research')
const stream = ref(true)
const webSearch = ref(false)
const systemPrompt = ref(
  'You are Career Intelligence, a helpful career coach. Use the selected resume and job descriptions to give specific, actionable advice.',
)

const draft = ref('')
const suggestions = [
  'What skills am I missing?',
  'Give me interview preparation tips',
  'Compare with second job',
  'Rewrite my summary',
]

const messages = ref<ChatMessageType[]>([
  {
    id: 'u1',
    role: 'user',
    time: '2:14 PM',
    text: 'How well does my resume match the Senior AI Engineer role at Acme Corp?',
  },
  {
    id: 'a1',
    role: 'assistant',
    time: '2:14 PM',
    text: 'Your resume is a strong fit for Senior AI Engineer at Acme Corp. You already cover the core GenAI and platform work they describe, with a few gaps to close before interviews.',
    strengths: [
      'Hands-on LLM application work and retrieval-style pipelines',
      'Python, cloud, and production service experience',
      'Evidence of shipping AI features with stakeholders',
    ],
    gaps: [
      'Limited mention of large-scale model evaluation or red-teaming',
      'Acme lists Kubernetes-heavy platform ownership that is only implied on your resume',
    ],
    sources: [
      { id: 's1', label: 'John_Doe_Resume.pdf' },
      { id: 's2', label: 'Senior AI Engineer - Acme Corp.pdf' },
    ],
  },
])

function send(text = draft.value) {
  const value = text.trim()
  if (!value) return
  messages.value.push({
    id: `u-${Date.now()}`,
    role: 'user',
    time: 'Just now',
    text: value,
  })
  draft.value = ''
  messages.value.push({
    id: `a-${Date.now()}`,
    role: 'assistant',
    time: 'Just now',
    text: `Using temperature ${temperature.value.toFixed(1)} and the selected documents, I would next break down ${value.toLowerCase()} against your resume and the chosen job descriptions.`,
    sources: [{ id: 's-resume', label: 'Selected resume' }, { id: 's-jobs', label: `${selectedJobIds.value.length} job descriptions` }],
  })
}
</script>

<template>
  <DashboardLayout show-recent-chats>
        <section class="flex h-full min-h-0 flex-col">
          <header class="shrink-0 px-6 pt-6 pb-3">
            <h1 class="text-[1.65rem] font-extrabold tracking-tight text-slate-900">Chat with Your Career Data</h1>
            <p class="mt-1 max-w-2xl text-sm text-slate-500">
              Ask questions about your resume and selected job descriptions. Document choices live in the right panel.
            </p>
          </header>

          <div id="chat-scroll" class="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-2">
            <ChatMessage v-for="message in messages" :key="message.id" :message="message" />
          </div>

          <div class="shrink-0 px-6 pt-2">
            <div class="flex flex-wrap gap-2 pb-3">
              <button
                v-for="item in suggestions"
                :key="item"
                class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-brand hover:text-brand"
                type="button"
                @click="send(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>
          <ChatComposer v-model:draft="draft" v-model:model="model" @send="send()" />
        </section>

        <template #right>
        <ChatRightPanel
          v-model:tab="tab"
          v-model:resume-id="selectedResumeId"
          v-model:job-ids="selectedJobIds"
          v-model:temperature="temperature"
          v-model:top-p="topP"
          v-model:max-tokens="maxTokens"
          v-model:model="model"
          v-model:stream="stream"
          v-model:web-search="webSearch"
          v-model:system-prompt="systemPrompt"
          @ask="send"
        />
        </template>
  </DashboardLayout>
</template>
