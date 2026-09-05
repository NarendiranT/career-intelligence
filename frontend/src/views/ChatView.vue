<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getConversation, listConversations } from '@/api/conversations'
import { fetchDocumentFile, listDocuments } from '@/api/documents'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatRightPanel from '@/components/chat/ChatRightPanel.vue'
import SampleDocumentModal from '@/components/upload/SampleDocumentModal.vue'
import {
  applyDocumentUpdate,
  removeDocument,
  useDocumentRealtime,
  type DocumentRealtimeEvent,
} from '@/composables/useDocumentRealtime'
import { useChatRealtime } from '@/composables/useChatRealtime'
import { showToast } from '@/composables/useToast'
import type {
  ChatMessage as ChatMessageType,
  ChatSocketEvent,
  ChatSource,
  ConversationDetail,
  ConversationMessage,
  ConversationSummary,
} from '@/types/chat'
import type { ApiDocument } from '@/types/document'

const CONTEXT_KEY = 'ci.chatDocumentContext'
const ALLOWED_MODEL = 'deep-research'

type StoredChatContext = { resumeId: string; jobIds: string[] }
type PreviewState = {
  title: string
  src: string
  text: string
  unavailable: boolean
  openLabel: string
}

const route = useRoute()
const router = useRouter()
const tab = ref<'documents' | 'settings'>('documents')
const selectedResumeId = ref('')
const selectedJobIds = ref<string[]>([])
const temperature = ref(0.7)
const topP = ref(1)
const maxTokens = ref(1024)
const model = ref(ALLOWED_MODEL)
const stream = ref(true)
const webSearch = ref(false)
const systemPrompt = ref(
  'You are Career Intelligence, a helpful career coach. Use the selected resume and job descriptions to give specific, actionable advice.',
)

const draft = ref('')
const documents = ref<ApiDocument[]>([])
const documentsLoading = ref(true)
const sending = ref(false)
const conversationId = ref<string | null>(null)
const assistantId = ref<string | null>(null)
const messages = ref<ChatMessageType[]>([])
const recentConversations = ref<ConversationSummary[]>([])
const threadLoading = ref(false)
const preview = ref<PreviewState | null>(null)

const suggestions = [
  'What skills am I missing?',
  'Give me interview preparation tips',
  'Compare with second job',
  'Rewrite my summary',
]

const processedResumes = computed(() =>
  documents.value.filter((doc) => doc.doc_type !== 'job' && doc.status === 'processed'),
)
const processedJobs = computed(() =>
  documents.value.filter((doc) => doc.doc_type === 'job' && doc.status === 'processed'),
)

const canAsk = computed(
  () => Boolean(selectedResumeId.value) && selectedJobIds.value.length > 0 && !sending.value,
)

const previewOpen = computed(() => preview.value !== null)

function clockTime(iso?: string | null): string {
  const date = iso ? new Date(iso) : new Date()
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function queryConversationId(): string | null {
  const value = route.query.conversation
  return typeof value === 'string' && value ? value : null
}

function contextStorageKey(id: string | null): string {
  return id ?? 'new'
}

function readStoredContext(id: string | null): StoredChatContext | null {
  try {
    const raw = localStorage.getItem(CONTEXT_KEY)
    if (!raw) return null
    const map = JSON.parse(raw) as Record<string, StoredChatContext>
    return map[contextStorageKey(id)] ?? null
  } catch {
    return null
  }
}

function writeStoredContext(id: string | null, ctx: StoredChatContext): void {
  try {
    const raw = localStorage.getItem(CONTEXT_KEY)
    const map = raw ? (JSON.parse(raw) as Record<string, StoredChatContext>) : {}
    map[contextStorageKey(id)] = ctx
    localStorage.setItem(CONTEXT_KEY, JSON.stringify(map))
  } catch {
    /* ignore quota / private mode */
  }
}

function persistSelection(): void {
  writeStoredContext(conversationId.value, {
    resumeId: selectedResumeId.value,
    jobIds: [...selectedJobIds.value],
  })
}

function applyContext(ctx: StoredChatContext | null | undefined): void {
  if (!ctx) return
  if (ctx.resumeId) selectedResumeId.value = ctx.resumeId
  if (ctx.jobIds?.length) selectedJobIds.value = [...ctx.jobIds]
  pruneSelection()
}

function toUiMessage(message: ConversationMessage): ChatMessageType {
  const extra = message.extra
  return {
    id: message.id,
    role: message.role,
    time: clockTime(message.created_at),
    text: message.content,
    strengths: extra?.strengths,
    gaps: extra?.gaps,
    sources: message.citations,
    usage: extra?.usage,
  }
}

async function loadConversations(): Promise<void> {
  try {
    recentConversations.value = await listConversations()
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not load conversations', 'error')
  }
}

async function openConversation(id: string): Promise<void> {
  if (sending.value) return
  if (conversationId.value === id && messages.value.length) return
  threadLoading.value = true
  try {
    const detail: ConversationDetail = await getConversation(id)
    conversationId.value = detail.id
    messages.value = detail.messages.map(toUiMessage)
    assistantId.value = null
    applyContext({
      resumeId: detail.resume_id || readStoredContext(detail.id)?.resumeId || '',
      jobIds: detail.job_ids?.length ? detail.job_ids : (readStoredContext(detail.id)?.jobIds ?? []),
    })
    persistSelection()
    scrollThread()
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not load conversation', 'error')
    await startNewChat()
  } finally {
    threadLoading.value = false
  }
}

async function startNewChat(updateRoute = true): Promise<void> {
  if (sending.value) return
  persistSelection()
  conversationId.value = null
  assistantId.value = null
  messages.value = []
  persistSelection()
  if (updateRoute && queryConversationId()) {
    await router.replace({ path: '/chat' })
  }
}

function selectConversation(id: string): void {
  if (sending.value || id === queryConversationId()) return
  persistSelection()
  void router.replace({ path: '/chat', query: { conversation: id } })
}

function pruneSelection(): void {
  if (documentsLoading.value) return
  const resumeIds = new Set(processedResumes.value.map((doc) => doc.id))
  const jobIds = new Set(processedJobs.value.map((doc) => doc.id))
  if (selectedResumeId.value && !resumeIds.has(selectedResumeId.value)) {
    selectedResumeId.value = processedResumes.value[0]?.id ?? ''
  }
  selectedJobIds.value = selectedJobIds.value.filter((id) => jobIds.has(id))
}

async function loadDocuments(): Promise<void> {
  documentsLoading.value = true
  try {
    documents.value = await listDocuments()
    documentsLoading.value = false
    pruneSelection()
    if (!queryConversationId() && !selectedResumeId.value && processedResumes.value[0]) {
      selectedResumeId.value = processedResumes.value[0].id
    }
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not load documents', 'error')
    documentsLoading.value = false
  }
}

function onDocumentEvent(event: DocumentRealtimeEvent): void {
  if (event.type === 'document.status') {
    documents.value = applyDocumentUpdate(documents.value, event.document)
  } else {
    documents.value = removeDocument(documents.value, event.document_id)
  }
  pruneSelection()
}

useDocumentRealtime(onDocumentEvent)

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
  persistSelection()
  const id = assistantId.value
  const target = id ? messages.value.find((item) => item.id === id) : undefined
  if (target) {
    target.pending = false
    target.text = event.text
    target.strengths = event.strengths
    target.gaps = event.gaps
    target.sources = event.citations
    target.usage = event.usage
    target.time = clockTime()
  }
  assistantId.value = null
  if (event.conversation_id && queryConversationId() !== event.conversation_id) {
    void router.replace({ path: '/chat', query: { conversation: event.conversation_id } })
  }
  void loadConversations()
  scrollThread()
}

const { connected, sendAsk } = useChatRealtime(onChatEvent)

function scrollThread(): void {
  void nextTick(() => {
    const el = document.getElementById('chat-scroll')
    if (el) el.scrollTop = el.scrollHeight
  })
}

function send(text = draft.value): void {
  const value = text.trim()
  if (!value || sending.value) return
  if (!selectedResumeId.value || selectedJobIds.value.length === 0) {
    showToast('Select a processed resume and at least one job description first.', 'error')
    tab.value = 'documents'
    return
  }
  if (!connected.value) {
    showToast('Chat is reconnecting. Try again in a moment.', 'error')
    return
  }

  persistSelection()
  messages.value.push({
    id: `u-${Date.now()}`,
    role: 'user',
    time: clockTime(),
    text: value,
  })
  draft.value = ''
  const replyId = `a-${Date.now()}`
  assistantId.value = replyId
  sending.value = true
  messages.value.push({
    id: replyId,
    role: 'assistant',
    time: clockTime(),
    text: '',
    pending: true,
  })
  scrollThread()

  const ok = sendAsk({
    question: value,
    resume_id: selectedResumeId.value,
    job_ids: selectedJobIds.value,
    conversation_id: conversationId.value,
    stream: stream.value,
    temperature: temperature.value,
    top_p: topP.value,
    max_tokens: maxTokens.value,
    system_prompt: systemPrompt.value,
    web_search: webSearch.value,
    model: ALLOWED_MODEL,
  })
  if (!ok) {
    sending.value = false
    assistantId.value = null
    const target = messages.value.find((item) => item.id === replyId)
    if (target) {
      target.pending = false
      target.text = 'Could not reach the assistant. Check that the API is running.'
    }
  }
}

function closePreview(): void {
  const current = preview.value
  preview.value = null
  if (current?.src.startsWith('blob:')) URL.revokeObjectURL(current.src)
}

async function previewSource(source: ChatSource): Promise<void> {
  const documentId = source.id?.trim()
  if (!documentId) {
    showToast('This source is missing a document id.', 'error')
    return
  }
  try {
    const file = await fetchDocumentFile(documentId)
    closePreview()
    const src = URL.createObjectURL(file.blob)
    const name = source.label.split(/[/\\]/).pop() || file.filename
    const mime = file.mime.toLowerCase()
    const isPdf = mime.includes('pdf') || name.toLowerCase().endsWith('.pdf')
    const isText =
      mime.startsWith('text/') || name.toLowerCase().endsWith('.txt') || mime.includes('json')
    let text = ''
    if (isText) text = await file.blob.text()
    preview.value = {
      title: name,
      src,
      text,
      unavailable: !isPdf && !isText,
      openLabel: isPdf ? 'Open PDF' : 'Open file',
    }
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not open the document', 'error')
  }
}

watch([processedResumes, processedJobs], pruneSelection)
watch([selectedResumeId, selectedJobIds], persistSelection, { deep: true })
watch(model, (value) => {
  if (value !== ALLOWED_MODEL) model.value = ALLOWED_MODEL
})
watch(
  () => route.query.conversation,
  (value) => {
    const id = typeof value === 'string' && value ? value : null
    if (!id) {
      if (!sending.value && conversationId.value) {
        persistSelection()
        conversationId.value = null
        messages.value = []
        assistantId.value = null
        persistSelection()
      }
      return
    }
    void openConversation(id)
  },
)

onMounted(() => {
  if (!queryConversationId()) applyContext(readStoredContext(null))
  void loadDocuments()
  void loadConversations()
  const id = queryConversationId()
  if (id) void openConversation(id)
})

onUnmounted(() => {
  closePreview()
})
</script>

<template>
  <DashboardLayout
    show-recent-chats
    :recent-chats="recentConversations"
    :active-conversation-id="conversationId"
    @select-conversation="selectConversation"
    @new-chat="startNewChat()"
  >
        <section class="flex h-full min-h-0 flex-col">
          <header class="shrink-0 px-6 pt-6 pb-3">
            <h1 class="text-[1.65rem] font-extrabold tracking-tight text-slate-900">Chat with Your Career Data</h1>
            <p class="mt-1 max-w-2xl text-sm text-slate-500">
              Select a resume and job descriptions, then ask a question. Answers are grounded in those documents.
            </p>
          </header>

          <div id="chat-scroll" class="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-2">
            <div
              v-if="threadLoading"
              class="flex h-full min-h-40 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 px-6 text-center"
            >
              <p class="text-sm font-medium text-slate-700">Loading conversation…</p>
            </div>
            <div
              v-else-if="!messages.length"
              class="flex h-full min-h-40 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 px-6 text-center"
            >
              <p class="text-sm font-medium text-slate-700">No messages yet</p>
              <p class="mt-1 max-w-md text-sm text-slate-500">
                {{
                  documentsLoading
                    ? 'Loading your documents…'
                    : canAsk
                      ? 'Ask a question about the selected resume and job descriptions.'
                      : 'Pick a processed resume and at least one job description in the right panel, then ask a question.'
                }}
              </p>
            </div>
            <template v-else>
              <ChatMessage
                v-for="message in messages"
                :key="message.id"
                :message="message"
                @preview-source="previewSource"
              />
            </template>
          </div>

          <div class="shrink-0 px-6 pt-2">
            <div class="flex flex-wrap gap-2 pb-3">
              <button
                v-for="item in suggestions"
                :key="item"
                class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-brand hover:text-brand disabled:opacity-40"
                type="button"
                :disabled="sending"
                @click="send(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>
          <ChatComposer
            v-model:draft="draft"
            v-model:model="model"
            v-model:web-search="webSearch"
            :disabled="sending"
            @send="send()"
          />
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
          v-model:system-prompt="systemPrompt"
          :documents="documents"
          :loading="documentsLoading"
          @ask="send"
        />
        </template>
  </DashboardLayout>

  <SampleDocumentModal
    :open="previewOpen"
    :title="preview?.title ?? ''"
    :src="preview?.src ?? ''"
    :text="preview?.text ?? ''"
    :unavailable="preview?.unavailable ?? false"
    :open-label="preview?.openLabel ?? 'Open file'"
    @close="closePreview"
  />
</template>
