<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bookmark, LoaderCircle, Trash2 } from '@lucide/vue'
import { getConversation, listConversations, bookmarkConversation, deleteConversation } from '@/api/conversations'
import { fetchDocumentFile, fetchDocumentText, listDocuments } from '@/api/documents'
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
import { resolveSourceDocument, sourceFileName } from '@/utils/chatSources'

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
const extractingTopics = ref(false)
const extractingFromId = ref<string | null>(null)
const conversationId = ref<string | null>(null)
const assistantId = ref<string | null>(null)
const messages = ref<ChatMessageType[]>([])
const recentConversations = ref<ConversationSummary[]>([])
const threadLoading = ref(false)
const threadBookmarked = ref(false)
const pendingDelete = ref<ConversationSummary | null>(null)
const deletingChat = ref(false)
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
    validated: extra?.validated === true,
    topics: extra?.topics,
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
    threadBookmarked.value = Boolean(detail.bookmarked)
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
  extractingFromId.value = null
  extractingTopics.value = false
  messages.value = []
  threadBookmarked.value = false
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

function clearStoredContext(id: string): void {
  try {
    const raw = localStorage.getItem(CONTEXT_KEY)
    if (!raw) return
    const map = JSON.parse(raw) as Record<string, StoredChatContext>
    delete map[id]
    localStorage.setItem(CONTEXT_KEY, JSON.stringify(map))
  } catch {
    /* ignore quota / private mode */
  }
}

async function toggleBookmark(id: string, bookmarked: boolean): Promise<void> {
  if (sending.value) return
  try {
    const updated = await bookmarkConversation(id, bookmarked)
    recentConversations.value = recentConversations.value.map((chat) =>
      chat.id === id ? { ...chat, bookmarked: updated.bookmarked } : chat,
    )
    if (conversationId.value === id) threadBookmarked.value = Boolean(updated.bookmarked)
    showToast(updated.bookmarked ? 'Saved to results' : 'Removed from saved results', 'success', 2000)
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not update bookmark', 'error')
  }
}

function requestDelete(id: string): void {
  if (sending.value || deletingChat.value) return
  const chat = recentConversations.value.find((item) => item.id === id)
  pendingDelete.value = chat ?? { id, title: 'This conversation', updated_at: null }
}

function cancelDelete(): void {
  if (deletingChat.value) return
  pendingDelete.value = null
}

async function confirmDeleteChat(): Promise<void> {
  const target = pendingDelete.value
  if (!target || deletingChat.value) return
  deletingChat.value = true
  try {
    await deleteConversation(target.id)
    clearStoredContext(target.id)
    recentConversations.value = recentConversations.value.filter((chat) => chat.id !== target.id)
    pendingDelete.value = null
    showToast('Conversation deleted', 'success', 2000)
    if (conversationId.value === target.id) await startNewChat()
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not delete conversation', 'error')
  } finally {
    deletingChat.value = false
  }
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
  if (extractingTopics.value) {
    if (event.type === 'chat.status' || event.type === 'chat.token') return
    extractingTopics.value = false
    const sourceId = extractingFromId.value
    extractingFromId.value = null
    if (event.type === 'chat.error') {
      showToast(event.detail, 'error')
      return
    }
    const created = event.topics ?? []
    if (!created.length) {
      showToast('Could not create interview topics from that reply', 'error')
      return
    }
    if (sourceId) {
      const source = messages.value.find((item) => item.id === sourceId)
      if (source) source.topics = created
    }
    showToast(
      event.topics_existing
        ? 'Interview topics already exist for this reply'
        : `Created ${created.length} interview topic${created.length === 1 ? '' : 's'}`,
      'success',
      2000,
    )
    void router.push({ path: '/interview', query: { topic: created[0].id } })
    return
  }
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
    target.validated = event.validated === true
    target.time = clockTime()
    if (event.message_id) target.id = event.message_id
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
  if (!value || sending.value || extractingTopics.value) return
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
    channel: 'assistant',
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

function prepareFromMessage(message: ChatMessageType): void {
  if (extractingTopics.value || sending.value || !message.text.trim() || !message.validated) return
  if (message.topics?.length) {
    void router.push({ path: '/interview', query: { topic: message.topics[0].id } })
    return
  }
  if (!connected.value) {
    showToast('Chat is reconnecting. Try again in a moment.', 'error')
    return
  }
  const extras: string[] = []
  if (message.strengths?.length) extras.push(`Strengths: ${message.strengths.join('; ')}`)
  if (message.gaps?.length) extras.push(`Gaps: ${message.gaps.join('; ')}`)
  const question = extras.length ? `${message.text.trim()}\n\n${extras.join('\n')}` : message.text.trim()
  extractingTopics.value = true
  extractingFromId.value = message.id
  const sourceMessageId = /^[0-9a-f-]{36}$/i.test(message.id) ? message.id : null
  const ok = sendAsk({
    question,
    resume_id: selectedResumeId.value || null,
    job_ids: selectedJobIds.value,
    conversation_id: conversationId.value,
    stream: true,
    temperature: temperature.value,
    top_p: topP.value,
    max_tokens: maxTokens.value,
    system_prompt: systemPrompt.value,
    web_search: false,
    model: ALLOWED_MODEL,
    channel: 'extract_topics',
    source_conversation_id: conversationId.value,
    source_message_id: sourceMessageId,
  })
  if (!ok) {
    extractingTopics.value = false
    extractingFromId.value = null
    showToast('Could not reach the assistant. Check that the API is running.', 'error')
  }
}

function closePreview(): void {
  const current = preview.value
  preview.value = null
  if (current?.src.startsWith('blob:')) URL.revokeObjectURL(current.src)
}

function sourceContext() {
  return {
    documents: documents.value,
    resumeId: selectedResumeId.value,
    jobIds: selectedJobIds.value,
  }
}

async function previewSource(source: ChatSource): Promise<void> {
  const document = resolveSourceDocument(source, sourceContext())
  const documentId = document?.id || null
  if (!documentId) {
    showToast('Could not match this source to an uploaded file.', 'error')
    return
  }
  try {
    const file = await fetchDocumentFile(documentId)
    closePreview()
    const src = URL.createObjectURL(file.blob)
    const uploadedName = document?.filename
    const name = uploadedName || file.filename || sourceFileName(source, sourceContext()) || documentId
    const mime = file.mime.toLowerCase()
    const isPdf = mime.includes('pdf') || name.toLowerCase().endsWith('.pdf')
    const isPlainText =
      mime.startsWith('text/') || name.toLowerCase().endsWith('.txt') || mime.includes('json')
    const needsExtractedText =
      !isPdf &&
      !isPlainText &&
      (name.toLowerCase().endsWith('.docx') || name.toLowerCase().endsWith('.doc') || mime.includes('word'))

    let text = ''
    if (isPlainText) text = await file.blob.text()
    else if (needsExtractedText) {
      const extracted = await fetchDocumentText(documentId)
      text = extracted.text
    }

    preview.value = {
      title: name,
      src,
      text,
      unavailable: !isPdf && !text,
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

function onWindowKey(event: KeyboardEvent): void {
  if (event.key === 'Escape' && pendingDelete.value) cancelDelete()
}

onMounted(() => {
  if (!queryConversationId()) applyContext(readStoredContext(null))
  void loadDocuments()
  void loadConversations()
  const id = queryConversationId()
  if (id) void openConversation(id)
  window.addEventListener('keydown', onWindowKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onWindowKey)
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
    @bookmark-conversation="toggleBookmark"
    @delete-conversation="requestDelete"
  >
        <section class="flex h-full min-h-0 flex-col">
          <header class="shrink-0 px-6 pt-6 pb-3">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h1 class="text-[1.65rem] font-extrabold tracking-tight text-slate-900">Chat with Your Career Data</h1>
                <p class="mt-1 max-w-2xl text-sm text-slate-500">
                  Select a resume and job descriptions, then ask a question. Answers are grounded in those documents.
                </p>
              </div>
              <div v-if="conversationId" class="flex shrink-0 items-center gap-1">
                <button
                  class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:border-orange-300 hover:text-orange-600"
                  :class="threadBookmarked ? 'border-orange-200 bg-orange-50 text-orange-600' : ''"
                  type="button"
                  :aria-pressed="threadBookmarked"
                  @click="toggleBookmark(conversationId, !threadBookmarked)"
                >
                  <Bookmark class="h-3.5 w-3.5" :class="threadBookmarked ? 'fill-current' : ''" />
                  {{ threadBookmarked ? 'Saved' : 'Save result' }}
                </button>
                <button
                  class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:border-red-200 hover:text-red-600"
                  type="button"
                  @click="requestDelete(conversationId)"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                  Delete
                </button>
              </div>
            </div>
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
                :documents="documents"
                :resume-id="selectedResumeId"
                :job-ids="selectedJobIds"
                :preparing="extractingTopics && extractingFromId === message.id"
                @preview-source="previewSource"
                @prepare-interview="prepareFromMessage"
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
                :disabled="sending || extractingTopics"
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

  <Teleport to="body">
    <div
      v-if="pendingDelete"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-slate-900/50 p-4"
      role="presentation"
      @click.self="cancelDelete"
    >
      <div
        class="w-full max-w-md rounded-2xl bg-white p-6 shadow-[0_24px_64px_rgba(15,23,42,0.28)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-chat-title"
      >
        <h2 id="delete-chat-title" class="text-lg font-bold text-slate-900">Delete this chat?</h2>
        <p class="mt-2 text-sm text-slate-500">
          <span class="font-medium text-slate-800">{{ pendingDelete.title }}</span>
          will be removed from recent chats and saved results. This cannot be undone.
        </p>
        <div class="mt-6 flex justify-end gap-3">
          <button
            class="rounded-xl px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            type="button"
            :disabled="deletingChat"
            @click="cancelDelete"
          >
            Cancel
          </button>
          <button
            class="inline-flex items-center gap-2 rounded-xl bg-red-500 px-4 py-2 text-sm font-semibold text-white hover:bg-red-600 disabled:opacity-50"
            type="button"
            :disabled="deletingChat"
            @click="confirmDeleteChat"
          >
            <LoaderCircle v-if="deletingChat" class="h-4 w-4 animate-spin" />
            Delete
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
