<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, FileText, Search } from '@lucide/vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'

type DocStatus = 'processed' | 'uploaded' | 'processing'
type DocTab = 'resumes' | 'jobs'

type LibraryFile = {
  id: string
  name: string
  sizeLabel: string
  uploadedLabel: string
  status: DocStatus
}

const tab = ref<DocTab>('resumes')
const query = ref('')
const page = ref(1)
const pageSize = 5

const resumes: LibraryFile[] = [
  {
    id: 'resume-1',
    name: 'John_Doe_Resume.pdf',
    sizeLabel: '245 KB',
    uploadedLabel: 'Uploaded 2 hours ago',
    status: 'processed',
  },
  {
    id: 'resume-2',
    name: 'software-engineer-resume.pdf',
    sizeLabel: '198 KB',
    uploadedLabel: 'Uploaded just now',
    status: 'uploaded',
  },
  {
    id: 'resume-3',
    name: 'Cover_Letter_Draft.docx',
    sizeLabel: '86 KB',
    uploadedLabel: 'Uploaded 5 days ago',
    status: 'processing',
  },
]

const jobs: LibraryFile[] = [
  {
    id: 'job-1',
    name: 'Senior AI Engineer - Acme Corp.pdf',
    sizeLabel: '312 KB',
    uploadedLabel: 'Uploaded 2 minutes ago',
    status: 'uploaded',
  },
  {
    id: 'job-2',
    name: 'Machine Learning Engineer - TechCo.pdf',
    sizeLabel: '428 KB',
    uploadedLabel: 'Uploaded 3 minutes ago',
    status: 'processed',
  },
  {
    id: 'job-3',
    name: 'GenAI Platform Engineer - InnovateAI.pdf',
    sizeLabel: '276 KB',
    uploadedLabel: 'Uploaded 4 minutes ago',
    status: 'processed',
  },
  {
    id: 'job-4',
    name: 'Senior_AI_Engineer_JD.pdf',
    sizeLabel: '301 KB',
    uploadedLabel: 'Uploaded 1 day ago',
    status: 'processed',
  },
  {
    id: 'job-5',
    name: 'Staff Backend Engineer - CloudNine.pdf',
    sizeLabel: '254 KB',
    uploadedLabel: 'Uploaded 2 days ago',
    status: 'processed',
  },
  {
    id: 'job-6',
    name: 'Applied Scientist - Northstar.pdf',
    sizeLabel: '389 KB',
    uploadedLabel: 'Uploaded 4 days ago',
    status: 'processed',
  },
  {
    id: 'job-7',
    name: 'LLM Platform Engineer - Helix.pdf',
    sizeLabel: '221 KB',
    uploadedLabel: 'Uploaded 1 week ago',
    status: 'uploaded',
  },
  {
    id: 'job-8',
    name: 'Data Scientist - BrightPath.pdf',
    sizeLabel: '198 KB',
    uploadedLabel: 'Uploaded 1 week ago',
    status: 'processed',
  },
  {
    id: 'job-9',
    name: 'MLOps Engineer - Orbit Labs.pdf',
    sizeLabel: '267 KB',
    uploadedLabel: 'Uploaded 2 weeks ago',
    status: 'processing',
  },
  {
    id: 'job-10',
    name: 'Product Engineer - InsightAI.pdf',
    sizeLabel: '184 KB',
    uploadedLabel: 'Uploaded 3 weeks ago',
    status: 'processed',
  },
]

const source = computed(() => (tab.value === 'resumes' ? resumes : jobs))

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return source.value
  return source.value.filter(
    (row) =>
      row.name.toLowerCase().includes(q) ||
      row.status.toLowerCase().includes(q) ||
      row.sizeLabel.toLowerCase().includes(q),
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))

const rows = computed(() => {
  if (tab.value === 'resumes') return filtered.value
  const start = (page.value - 1) * pageSize
  return filtered.value.slice(start, start + pageSize)
})

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

function statusClass(status: DocStatus) {
  if (status === 'processed') return 'bg-emerald-50 text-emerald-600'
  if (status === 'processing') return 'bg-blue-50 text-brand'
  return 'bg-slate-100 text-slate-600'
}

function statusLabel(status: DocStatus) {
  if (status === 'processed') return 'Processed'
  if (status === 'processing') return 'Processing'
  return 'Uploaded'
}
</script>

<template>
  <DashboardLayout>
    <div id="documents-scroll" class="h-full overflow-y-auto p-6 xl:p-8">
      <p class="text-[11px] font-bold tracking-[0.16em] text-brand uppercase">Library</p>
      <h1 class="mt-1 text-[1.65rem] font-extrabold text-slate-800">My Documents</h1>
      <p class="mt-2 max-w-2xl text-sm text-slate-500">
        Browse resumes and job descriptions already in this workspace. Search either tab; job
        descriptions are paginated.
      </p>

      <div class="mt-6 rounded-2xl border border-slate-100 bg-white shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
        <div class="flex flex-col gap-4 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex gap-1 rounded-xl bg-slate-100 p-1">
            <button
              class="rounded-lg px-3 py-2 text-sm font-semibold"
              :class="tab === 'resumes' ? 'bg-white text-brand shadow-sm' : 'text-slate-500'"
              type="button"
              @click="tab = 'resumes'"
            >
              My Resumes
              <span class="ml-1 text-[11px] font-medium text-slate-400">({{ resumes.length }})</span>
            </button>
            <button
              class="rounded-lg px-3 py-2 text-sm font-semibold"
              :class="tab === 'jobs' ? 'bg-white text-brand shadow-sm' : 'text-slate-500'"
              type="button"
              @click="tab = 'jobs'"
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
              </tr>
            </thead>
            <tbody>
              <tr v-if="rows.length === 0">
                <td class="px-5 py-10 text-center text-slate-400" colspan="4">No documents match your search.</td>
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
                    <span class="font-medium text-slate-800">{{ row.name }}</span>
                  </div>
                </td>
                <td class="px-5 py-3 text-slate-500">{{ row.sizeLabel }}</td>
                <td class="px-5 py-3 text-slate-500">{{ row.uploadedLabel }}</td>
                <td class="px-5 py-3">
                  <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold capitalize" :class="statusClass(row.status)">
                    {{ statusLabel(row.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="tab === 'jobs'"
          class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3"
        >
          <p class="text-xs text-slate-400">
            Showing {{ rows.length }} of {{ filtered.length }} job descriptions
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
  </DashboardLayout>
</template>
