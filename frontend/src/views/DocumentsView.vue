<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft, ChevronRight, FileText, LoaderCircle, Search, Trash2 } from '@lucide/vue'
import { deleteDocument, listDocuments } from '@/api/documents'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import {
  applyDocumentUpdate,
  removeDocument,
  useDocumentRealtime,
  type DocumentRealtimeEvent,
} from '@/composables/useDocumentRealtime'
import { showToast } from '@/composables/useToast'
import type { ApiDocument, DocumentStatus } from '@/types/document'
import { formatBytes } from '@/types/upload'
import { formatRelativeTime } from '@/utils/time'

type DocTab = 'resumes' | 'jobs'

const PAGE_SIZE = 10

const route = useRoute()
const router = useRouter()
const tab = ref<DocTab>('resumes')
const query = ref('')
const page = ref(1)
const loading = ref(true)
const error = ref('')
const documents = ref<ApiDocument[]>([])
const pendingDelete = ref<ApiDocument | null>(null)
const deleting = ref(false)

const resumes = computed(() => documents.value.filter((doc) => doc.doc_type !== 'job'))
const jobs = computed(() => documents.value.filter((doc) => doc.doc_type === 'job'))
const source = computed(() => (tab.value === 'resumes' ? resumes.value : jobs.value))

function sizeLabel(doc: ApiDocument): string {
  return doc.size == null ? '—' : formatBytes(doc.size)
}

function uploadedLabel(doc: ApiDocument): string {
  const relative = formatRelativeTime(doc.created_at)
  return relative ? `Uploaded ${relative}` : 'Uploaded'
}

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return source.value
  return source.value.filter((row) => {
    const haystack = [row.filename, row.status, sizeLabel(row), uploadedLabel(row)].join(' ').toLowerCase()
    return haystack.includes(q)
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))

const rows = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filtered.value.slice(start, start + PAGE_SIZE)
})

function tabFromQuery(value: unknown): DocTab {
  const raw = Array.isArray(value) ? value[0] : value
  return raw === 'jobs' ? 'jobs' : 'resumes'
}

function setTab(next: DocTab) {
  tab.value = next
  void router.replace({
    path: '/documents',
    query: next === 'jobs' ? { tab: 'jobs' } : {},
  })
}

watch(
  () => route.query.tab,
  (value) => {
    tab.value = tabFromQuery(value)
  },
  { immediate: true },
)

watch(tab, () => {
  query.value = ''
  page.value = 1
})

watch(query, () => {
  page.value = 1
})

watch(totalPages, (next) => {
  if (page.value > next) page.value = next
})

function statusClass(status: DocumentStatus) {
  if (status === 'processed') return 'bg-emerald-50 text-emerald-600'
  if (status === 'processing') return 'bg-blue-50 text-brand'
  if (status === 'failed') return 'bg-red-50 text-red-500'
  return 'bg-slate-100 text-slate-600'
}

function statusLabel(status: DocumentStatus) {
  if (status === 'processed') return 'Processed'
  if (status === 'processing') return 'Processing'
  if (status === 'failed') return 'Failed'
  return 'Uploaded'
}

async function loadDocuments(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    documents.value = await listDocuments()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load documents.'
    documents.value = []
  } finally {
    loading.value = false
  }
}

function onDocumentEvent(event: DocumentRealtimeEvent): void {
  if (event.type === 'document.status' && event.document) {
    documents.value = applyDocumentUpdate(documents.value, event.document)
    return
  }
  if (event.type === 'document.deleted' && event.document_id) {
    documents.value = removeDocument(documents.value, event.document_id)
    if (pendingDelete.value?.id === event.document_id) {
      pendingDelete.value = null
    }
  }
}

useDocumentRealtime(onDocumentEvent)

async function confirmDelete(): Promise<void> {
  const target = pendingDelete.value
  if (!target || deleting.value) return
  deleting.value = true
  try {
    await deleteDocument(target.id)
    documents.value = removeDocument(documents.value, target.id)
    showToast(`Deleted ${target.filename}`, 'success')
    pendingDelete.value = null
  } catch (err) {
    showToast(err instanceof Error ? err.message : 'Could not delete this document.', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  void loadDocuments()
})
</script>

<template>
  <DashboardLayout>
    <div id="documents-scroll" class="h-full overflow-y-auto p-6 xl:p-8">
      <p class="text-[11px] font-bold tracking-[0.16em] text-brand uppercase">Library</p>
      <h1 class="mt-1 text-[1.65rem] font-extrabold text-slate-800">My Documents</h1>
      <p class="mt-2 max-w-2xl text-sm text-slate-500">
        Browse resumes and job descriptions already in this workspace. Indexing status updates live
        as each file is processed. Search either tab; results are shown 10 per page.
      </p>

      <p v-if="error" class="mt-6 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
        {{ error }}
        <button class="ml-2 font-semibold underline" type="button" @click="loadDocuments">Retry</button>
      </p>

      <div class="mt-6 rounded-2xl border border-slate-100 bg-white shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
        <div class="flex flex-col gap-4 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex gap-1 rounded-xl bg-slate-100 p-1">
            <button
              class="rounded-lg px-3 py-2 text-sm font-semibold"
              :class="tab === 'resumes' ? 'bg-white text-brand shadow-sm' : 'text-slate-500'"
              type="button"
              @click="setTab('resumes')"
            >
              My Resumes
              <span class="ml-1 text-[11px] font-medium text-slate-400">({{ resumes.length }})</span>
            </button>
            <button
              class="rounded-lg px-3 py-2 text-sm font-semibold"
              :class="tab === 'jobs' ? 'bg-white text-brand shadow-sm' : 'text-slate-500'"
              type="button"
              @click="setTab('jobs')"
            >
              Job Descriptions
              <span class="ml-1 text-[11px] font-medium text-slate-400">({{ jobs.length }})</span>
            </button>
          </div>
          <label class="relative w-full sm:max-w-xs">
            <Search class="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              v-model="query"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pr-3 pl-9 text-sm outline-none placeholder:text-slate-400 focus:border-brand focus:bg-white focus:ring-4 focus:ring-brand/10"
              type="search"
              :placeholder="tab === 'resumes' ? 'Search resumes...' : 'Search job descriptions...'"
            />
          </label>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full min-w-[640px] text-left text-sm">
            <thead class="border-b border-slate-100 bg-slate-50 text-[11px] font-semibold tracking-wide text-slate-400 uppercase">
              <tr>
                <th class="px-5 py-3">Name</th>
                <th class="px-5 py-3">Size</th>
                <th class="px-5 py-3">Uploaded</th>
                <th class="px-5 py-3">Status</th>
                <th class="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td class="px-5 py-10 text-center text-slate-400" colspan="5">
                  <span class="inline-flex items-center gap-2">
                    <LoaderCircle class="h-4 w-4 animate-spin" />
                    Loading documents…
                  </span>
                </td>
              </tr>
              <tr v-else-if="source.length === 0">
                <td class="px-5 py-10 text-center text-slate-400" colspan="5">
                  No {{ tab === 'resumes' ? 'resumes' : 'job descriptions' }} yet.
                  <RouterLink to="/upload" class="font-semibold text-brand hover:underline">Upload one</RouterLink>
                </td>
              </tr>
              <tr v-else-if="rows.length === 0">
                <td class="px-5 py-10 text-center text-slate-400" colspan="5">No documents match your search.</td>
              </tr>
              <tr v-for="row in rows" :key="row.id" class="border-b border-slate-50 last:border-0">
                <td class="px-5 py-3">
                  <div class="flex items-center gap-3">
                    <span
                      class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                      :class="tab === 'resumes' ? 'bg-red-50 text-red-500' : 'bg-blue-50 text-brand'"
                    >
                      <FileText class="h-4 w-4" />
                    </span>
                    <span class="font-medium text-slate-800">{{ row.filename }}</span>
                  </div>
                </td>
                <td class="px-5 py-3 text-slate-500">{{ sizeLabel(row) }}</td>
                <td class="px-5 py-3 text-slate-500">{{ uploadedLabel(row) }}</td>
                <td class="px-5 py-3">
                  <span
                    class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold capitalize"
                    :class="statusClass(row.status)"
                    :title="row.error_message || undefined"
                  >
                    <LoaderCircle v-if="row.status === 'processing'" class="h-3 w-3 animate-spin" />
                    {{ statusLabel(row.status) }}
                  </span>
                </td>
                <td class="px-5 py-3 text-right">
                  <button
                    class="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-red-500 hover:bg-red-50"
                    type="button"
                    :aria-label="`Delete ${row.filename}`"
                    @click="pendingDelete = row"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                    Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3">
          <p class="text-xs text-slate-400">
            Showing {{ rows.length }} of {{ filtered.length }}
            {{ tab === 'resumes' ? 'resumes' : 'job descriptions' }}
          </p>
          <div class="flex items-center gap-1">
            <button
              class="rounded-lg p-1.5 text-slate-500 hover:bg-slate-50 disabled:opacity-40"
              type="button"
              :disabled="page <= 1"
              aria-label="Previous page"
              @click="page -= 1"
            >
              <ChevronLeft class="h-4 w-4" />
            </button>
            <span class="px-2 text-sm font-medium text-slate-600">{{ page }} / {{ totalPages }}</span>
            <button
              class="rounded-lg p-1.5 text-slate-500 hover:bg-slate-50 disabled:opacity-40"
              type="button"
              :disabled="page >= totalPages"
              aria-label="Next page"
              @click="page += 1"
            >
              <ChevronRight class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="pendingDelete"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-doc-title"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h2 id="delete-doc-title" class="text-lg font-bold text-slate-900">Delete this file?</h2>
        <p class="mt-2 text-sm text-slate-500">
          <span class="font-medium text-slate-800">{{ pendingDelete.filename }}</span>
          will be removed from your library, including indexed chunks. This cannot be undone.
        </p>
        <div class="mt-6 flex justify-end gap-3">
          <button
            class="rounded-xl px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            type="button"
            :disabled="deleting"
            @click="pendingDelete = null"
          >
            Cancel
          </button>
          <button
            class="inline-flex items-center gap-2 rounded-xl bg-red-500 px-4 py-2 text-sm font-semibold text-white hover:bg-red-600 disabled:opacity-50"
            type="button"
            :disabled="deleting"
            @click="confirmDelete"
          >
            <LoaderCircle v-if="deleting" class="h-4 w-4 animate-spin" />
            Delete
          </button>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>
