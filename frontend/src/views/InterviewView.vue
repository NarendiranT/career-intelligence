<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronDown, LoaderCircle } from '@lucide/vue'
import { getConversation } from '@/api/conversations'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import InterviewComposer from '@/components/interview/InterviewComposer.vue'
import InterviewMessage from '@/components/interview/InterviewMessage.vue'
import InterviewRightPanel from '@/components/interview/InterviewRightPanel.vue'
import { useChatRealtime } from '@/composables/useChatRealtime'
import { useInterview } from '@/composables/useInterview'
import { showToast } from '@/composables/useToast'
import type { ChatSocketEvent, ConversationMessage } from '@/types/chat'
import {
  formatQuestionCount,
  interviewSystemPrompt,
  questionCountLabel,
  temperatureForDifficulty,
  type Difficulty,
  type InterviewMessage as InterviewMessageType,
  type InterviewMode,
  type ResponseStyle,
} from '@/types/interview'
import { normalizeCode, normalizeTable } from '@/utils/richText'

const ALLOWED_MODEL = 'deep-research'

const route = useRoute()
const router = useRouter()
const {
  selectedTopic,
  selectedTopicId,
  interviewTopics,
  topicsLoading,
  selectTopic,
  incrementQuestionCount,
  loadTopics,
} = useInterview()

const topicMenuOpen = ref(false)
const draft = ref('')
const model = ref(ALLOWED_MODEL)
const mode = ref<InterviewMode>('practice')
const responseStyle = ref<ResponseStyle>('detailed')
const difficulty = ref<Difficulty>('medium')
const includeCode = ref(true)
const followUps = ref(true)
const bestPractices = ref(true)
const messages = ref<InterviewMessageType[]>([])
const sending = ref(false)
const threadLoading = ref(false)
const assistantId = ref<string | null>(null)
const conversationId = ref<string | null>(null)

const roleLabel = computed(() => {
  const label = selectedTopic.value?.label
  if (!label) return 'Interview practice'
  if (/behavioral/i.test(label)) return 'Behavioral interview'
  return `Senior ${label} Developer`
})

const systemPrompt = computed(() =>
  interviewSystemPrompt({
    topicLabel: selectedTopic.value?.label || 'this topic',
    mode: mode.value,
    responseStyle: responseStyle.value,
    difficulty: difficulty.value,
    includeCode: includeCode.value,
    followUps: followUps.value,
    bestPractices: bestPractices.value,
  }),
)

function nowLabel(): string {
  return new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function greetingForTopic(): InterviewMessageType {
  const label = selectedTopic.value?.label || 'this topic'
  return {
    id: `a-${Date.now()}`,
    role: 'assistant',
    time: nowLabel(),
    text: `Let's practice ${label}. Ask a concept question, a comparison, or a coding problem and I will answer at ${difficulty.value} difficulty.`,
  }
}

function toUiMessage(message: ConversationMessage): InterviewMessageType {
  const stamp = message.created_at ? new Date(message.created_at) : new Date()
  const extra = message.extra
  return {
    id: message.id,
    role: message.role,
    time: stamp.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
    text: message.content,
    table: normalizeTable(extra?.table),
    code: normalizeCode(extra?.code),
  }
}

function queryTopicId(): string | null {
  const value = route.query.topic
  return typeof value === 'string' && value ? value : null
}

async function loadThread(): Promise<void> {
  const topic = selectedTopic.value
  const convoId = topic?.conversation_id
  conversationId.value = convoId ?? null
  if (!convoId) {
    messages.value = topic ? [greetingForTopic()] : []
    return
  }
  threadLoading.value = true
  try {
    const detail = await getConversation(convoId)
    conversationId.value = detail.id
    messages.value = detail.messages.length ? detail.messages.map(toUiMessage) : [greetingForTopic()]
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not load topic chat', 'error')
    messages.value = [greetingForTopic()]
  } finally {
    threadLoading.value = false
    scrollThread()
  }
}

function onChatEvent(event: ChatSocketEvent): void {
  if (event.type === 'chat.status') return
  if (event.type === 'chat.token') {
    const id = assistantId.value
    if (!id) return
    const target = messages.value.find((item) => item.id === id)
    if (target) target.text += event.text
    scrollThread()
    return
  }
  if (event.type === 'chat.error') {
    sending.value = false
    const id = assistantId.value
    if (id) {
      const target = messages.value.find((item) => item.id === id)
      if (target) {
        target.pending = false
        target.text = target.text || event.detail
      }
    }
    assistantId.value = null
    showToast(event.detail, 'error')
    return
  }
  sending.value = false
  conversationId.value = event.conversation_id
  const id = assistantId.value
  const target = id ? messages.value.find((item) => item.id === id) : undefined
  if (target) {
    target.pending = false
    target.text = event.text
    target.table = normalizeTable(event.table)
    target.code = normalizeCode(event.code)
    target.time = nowLabel()
  }
  assistantId.value = null
  scrollThread()
}

const { connected, sendAsk } = useChatRealtime(onChatEvent)

function scrollThread(): void {
  void nextTick(() => {
    const el = document.getElementById('interview-scroll')
    if (el) el.scrollTop = el.scrollHeight
  })
}

function send(text = draft.value): void {
  const value = text.trim()
  if (!value || sending.value) return
  const topic = selectedTopic.value
  if (!topic) {
    showToast('Create interview topics from Chat with Assistant first.', 'error')
    return
  }
  if (!connected.value) {
    showToast('Chat is reconnecting. Try again in a moment.', 'error')
    return
  }
  messages.value.push({
    id: `u-${Date.now()}`,
    role: 'user',
    time: nowLabel(),
    text: value,
  })
  draft.value = ''
  const replyId = `a-${Date.now()}`
  assistantId.value = replyId
  sending.value = true
  messages.value.push({
    id: replyId,
    role: 'assistant',
    time: nowLabel(),
    text: '',
    pending: true,
  })
  scrollThread()
  const ok = sendAsk({
    question: value,
    conversation_id: conversationId.value,
    stream: true,
    temperature: temperatureForDifficulty(difficulty.value),
    top_p: 1,
    max_tokens: 1024,
    system_prompt: systemPrompt.value,
    model: ALLOWED_MODEL,
    channel: 'interview',
    topic_id: topic.id,
  })
  if (!ok) {
    sending.value = false
    assistantId.value = null
    const target = messages.value.find((item) => item.id === replyId)
    if (target) {
      target.pending = false
      target.text = 'Could not reach the assistant. Check that the API is running.'
    }
    return
  }
  incrementQuestionCount(topic.id)
}

function clearChat(): void {
  messages.value = selectedTopic.value ? [greetingForTopic()] : []
}

function chooseTopic(id: string): void {
  topicMenuOpen.value = false
  selectTopic(id)
  void router.replace({ path: '/interview', query: { topic: id } })
}

watch(selectedTopicId, (id, previous) => {
  if (id === previous) return
  topicMenuOpen.value = false
  void loadThread()
})

watch(
  () => route.query.topic,
  (value) => {
    const id = typeof value === 'string' ? value : ''
    if (id && id !== selectedTopicId.value) selectTopic(id)
  },
)

onMounted(async () => {
  const loaded = await loadTopics()
  const requested = queryTopicId()
  if (requested && loaded.some((topic) => topic.id === requested)) {
    selectTopic(requested)
  } else if (selectedTopic.value) {
    void router.replace({ path: '/interview', query: { topic: selectedTopic.value.id } })
  }
  await loadThread()
})
</script>

<template>
  <DashboardLayout show-interview-topics>
    <section class="flex h-full min-h-0 flex-col">
      <header class="flex shrink-0 items-start justify-between gap-4 px-6 pt-6 pb-3">
        <div>
          <h1 class="text-[1.65rem] font-extrabold tracking-tight text-slate-900">
            {{ selectedTopic ? `${selectedTopic.label} Interview Preparation` : 'Prepare for Interviews' }}
          </h1>
          <p class="mt-1 max-w-2xl text-sm text-slate-500">
            Practice concepts, solve problems, and get expert guidance for your interviews.
          </p>
        </div>
        <div v-if="interviewTopics.length" class="relative shrink-0">
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
              class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50"
              :class="topic.id === selectedTopicId ? 'font-semibold text-brand' : 'text-slate-700'"
              type="button"
              :title="questionCountLabel(topic.question_count)"
              @click="chooseTopic(topic.id)"
            >
              <span class="min-w-0 flex-1 truncate">{{ topic.label }}</span>
              <span class="shrink-0 text-[11px] font-semibold tabular-nums text-slate-400">
                {{ formatQuestionCount(topic.question_count) }}
              </span>
            </button>
          </div>
        </div>
      </header>

      <div id="interview-scroll" class="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-2">
        <div v-if="topicsLoading || threadLoading" class="flex h-full min-h-40 items-center justify-center gap-2 text-slate-500">
          <LoaderCircle class="h-4 w-4 animate-spin" />
          <p class="text-sm">Loading topics…</p>
        </div>
        <div
          v-else-if="!interviewTopics.length"
          class="flex h-full min-h-40 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 px-6 text-center"
        >
          <p class="text-sm font-medium text-slate-700">No interview topics yet</p>
          <p class="mt-1 max-w-md text-sm text-slate-500">
            Chat with the assistant about your resume and jobs, then tap Prepare for interview on a reply.
          </p>
          <RouterLink
            class="mt-4 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white"
            to="/chat"
          >
            Chat with Assistant
          </RouterLink>
        </div>
        <template v-else>
          <InterviewMessage v-for="message in messages" :key="message.id" :message="message" />
        </template>
      </div>

      <InterviewComposer
        v-model:draft="draft"
        v-model:model="model"
        @send="send()"
      />
    </section>

    <template #right>
      <InterviewRightPanel
        v-model:mode="mode"
        v-model:response-style="responseStyle"
        v-model:difficulty="difficulty"
        v-model:include-code="includeCode"
        v-model:follow-ups="followUps"
        v-model:best-practices="bestPractices"
        :topic-label="selectedTopic?.label || 'None yet'"
        :role-label="roleLabel"
        @clear="clearChat"
      />
    </template>
  </DashboardLayout>
</template>
