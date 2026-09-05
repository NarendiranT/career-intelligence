<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronDown } from '@lucide/vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import InterviewComposer from '@/components/interview/InterviewComposer.vue'
import InterviewMessage from '@/components/interview/InterviewMessage.vue'
import InterviewRightPanel from '@/components/interview/InterviewRightPanel.vue'
import { useInterview } from '@/composables/useInterview'
import type {
  Difficulty,
  InterviewMessage as InterviewMessageType,
  InterviewMode,
  ResponseStyle,
} from '@/types/interview'

const { selectedTopic, selectedTopicId, interviewTopics, selectTopic } = useInterview()
const topicMenuOpen = ref(false)
const draft = ref('')
const model = ref('gpt-4o')
const mode = ref<InterviewMode>('practice')
const responseStyle = ref<ResponseStyle>('detailed')
const difficulty = ref<Difficulty>('medium')
const includeCode = ref(true)
const followUps = ref(true)
const bestPractices = ref(true)

const roleLabel = computed(() => {
  if (selectedTopic.value.id === 'behavioral') return 'Behavioral interview'
  return `Senior ${selectedTopic.value.label} Developer`
})

function nowLabel(): string {
  return new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function pythonSeed(): InterviewMessageType[] {
  return [
    {
      id: 'u-seed',
      role: 'user',
      time: '10:24 AM',
      text: 'Explain the difference between list and tuple in Python with examples.',
    },
    {
      id: 'a-seed',
      role: 'assistant',
      time: '10:25 AM',
      text: 'Lists and tuples are both ordered sequences, but they are built for different jobs. Use a list when the collection needs to change; use a tuple when the values should stay fixed.',
      table: {
        headers: ['Feature', 'List', 'Tuple'],
        rows: [
          ['Mutability', 'Mutable (can change)', 'Immutable (cannot change)'],
          ['Syntax', '[1, 2, 3]', '(1, 2, 3)'],
          ['Performance', 'Slightly slower to update', 'Faster and hashable when items are hashable'],
          ['Use case', 'Growing collections, records you edit', 'Fixed records, dict keys, unpacking'],
          ['Methods', 'append, pop, sort, …', 'count, index'],
        ],
      },
      code: {
        language: 'python',
        content: `skills = ["python", "fastapi"]  # list
skills.append("sql")

coords = (10.0, 20.0)  # tuple
# coords[0] = 11.0  # TypeError: tuples cannot be changed`,
      },
    },
  ]
}

function greetingForTopic(): InterviewMessageType {
  return {
    id: `a-${Date.now()}`,
    role: 'assistant',
    time: nowLabel(),
    text: `Let's practice ${selectedTopic.value.label}. Ask a concept question, a comparison, or a coding problem and I will answer at ${difficulty.value} difficulty.`,
  }
}

const messages = ref<InterviewMessageType[]>(pythonSeed())

watch(selectedTopicId, (id, previous) => {
  if (id === previous) return
  topicMenuOpen.value = false
  messages.value = id === 'python' ? pythonSeed() : [greetingForTopic()]
})

function send(text = draft.value): void {
  const value = text.trim()
  if (!value) return
  messages.value.push({
    id: `u-${Date.now()}`,
    role: 'user',
    time: nowLabel(),
    text: value,
  })
  draft.value = ''

  const extras: string[] = []
  if (includeCode.value) extras.push('Include a short code example when it helps.')
  if (followUps.value) extras.push(`Follow-up: What else should I know about this for a ${difficulty.value} interview?`)
  if (bestPractices.value) extras.push('Mention one best practice interviewers listen for.')

  messages.value.push({
    id: `a-${Date.now()}`,
    role: 'assistant',
    time: nowLabel(),
    text: [
      `${mode.value === 'mock' ? 'Mock interviewer:' : 'Practice coach:'} ${selectedTopic.value.label} · ${responseStyle.value} · ${difficulty.value}.`,
      '',
      `Here is a focused answer to “${value}”. Connect it to real ${selectedTopic.value.label} work you have shipped, then pause for the interviewer.`,
      extras.length ? `\n${extras.join(' ')}` : '',
    ].join('\n'),
  })
}

function clearChat(): void {
  messages.value = [greetingForTopic()]
}

function chooseTopic(id: string): void {
  topicMenuOpen.value = false
  selectTopic(id)
}
</script>

<template>
  <DashboardLayout show-interview-topics>
    <section class="flex h-full min-h-0 flex-col">
      <header class="flex shrink-0 items-start justify-between gap-4 px-6 pt-6 pb-3">
        <div>
          <h1 class="text-[1.65rem] font-extrabold tracking-tight text-slate-900">
            {{ selectedTopic.label }} Interview Preparation
          </h1>
          <p class="mt-1 max-w-2xl text-sm text-slate-500">
            Practice concepts, solve problems, and get expert guidance for your interviews.
          </p>
        </div>
        <div class="relative shrink-0">
          <button
            class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            type="button"
            @click="topicMenuOpen = !topicMenuOpen"
          >
            Change Topic
            <ChevronDown class="h-4 w-4 text-slate-400" />
          </button>
          <div
            v-if="topicMenuOpen"
            class="absolute right-0 z-20 mt-2 max-h-72 w-56 overflow-y-auto rounded-xl border border-slate-100 bg-white py-1 shadow-lg"
          >
            <button
              v-for="topic in interviewTopics"
              :key="topic.id"
              class="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50"
              :class="topic.id === selectedTopicId ? 'font-semibold text-brand' : 'text-slate-700'"
              type="button"
              @click="chooseTopic(topic.id)"
            >
              {{ topic.label }}
            </button>
          </div>
        </div>
      </header>

      <div id="interview-scroll" class="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-2">
        <InterviewMessage v-for="message in messages" :key="message.id" :message="message" />
      </div>

      <InterviewComposer v-model:draft="draft" v-model:model="model" @send="send()" />
    </section>

    <template #right>
      <InterviewRightPanel
        v-model:mode="mode"
        v-model:response-style="responseStyle"
        v-model:difficulty="difficulty"
        v-model:include-code="includeCode"
        v-model:follow-ups="followUps"
        v-model:best-practices="bestPractices"
        :topic-label="selectedTopic.label"
        :role-label="roleLabel"
        @clear="clearChat"
      />
    </template>
  </DashboardLayout>
</template>
