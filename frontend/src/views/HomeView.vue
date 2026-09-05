<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ArrowRight,
  BarChart3,
  Bookmark,
  Briefcase,
  FileText,
  Lightbulb,
  LoaderCircle,
  MessageSquare,
  Upload,
} from '@lucide/vue'
import { fetchHomeSummary } from '@/api/home'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { applyDocumentUpdate, removeDocument, useDocumentRealtime } from '@/composables/useDocumentRealtime'
import type { HomeConversation, HomeDocument, HomeStats } from '@/types/home'
import { formatRelativeTime } from '@/utils/time'

const emptyStats: HomeStats = {
  resume_count: 0,
  job_count: 0,
  insight_count: 0,
  saved_result_count: 0,
}

const loading = ref(true)
const error = ref('')
const documents = ref<HomeDocument[]>([])
const conversations = ref<HomeConversation[]>([])
const stats = ref<HomeStats>({ ...emptyStats })

function kindLabel(doc: HomeDocument): string {
  return doc.doc_type === 'job' ? 'Job Description' : 'Resume'
}

function uploadedLabel(doc: HomeDocument): string {
  const relative = formatRelativeTime(doc.created_at)
  return relative ? `Uploaded ${relative}` : 'Uploaded'
}

async function loadHome(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const summary = await fetchHomeSummary()
    documents.value = summary.documents
    conversations.value = summary.conversations
    stats.value = summary.stats
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load home.'
    documents.value = []
    conversations.value = []
    stats.value = { ...emptyStats }
  } finally {
    loading.value = false
  }
}

useDocumentRealtime((event) => {
  if (event.type === 'document.status') {
    documents.value = applyDocumentUpdate(documents.value, event.document)
    return
  }
  const removed = documents.value.find((row) => row.id === event.document_id)
  documents.value = removeDocument(documents.value, event.document_id)
  if (!removed) return
  if (removed.doc_type === 'job') {
    stats.value = { ...stats.value, job_count: Math.max(0, stats.value.job_count - 1) }
  } else if (removed.doc_type === 'resume') {
    stats.value = { ...stats.value, resume_count: Math.max(0, stats.value.resume_count - 1) }
  }
})

onMounted(() => {
  void loadHome()
})
</script>

<template>
  <DashboardLayout>
    <div id="home-scroll" class="h-full overflow-y-auto p-6 xl:p-8">
      <section
        class="relative overflow-hidden rounded-[28px] border border-blue-100 bg-gradient-to-br from-[#e8f1ff] via-[#f4f8ff] to-white px-6 py-8 sm:px-10 sm:py-10"
      >
        <div class="relative grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p class="text-[11px] font-bold tracking-[0.18em] text-brand uppercase">
              AI-Powered Career Assistant
            </p>
            <h1 class="mt-3 max-w-xl text-3xl font-extrabold tracking-tight text-slate-900 sm:text-[2.35rem] sm:leading-[1.15]">
              Turn Your Experience into
              <span class="text-brand">New Opportunities</span>
            </h1>
            <p class="mt-4 max-w-lg text-sm leading-relaxed text-slate-500 sm:text-[15px]">
              Upload your resume, add job descriptions, and get AI-powered insights, skill gap
              analysis, and personalized recommendations.
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
              <RouterLink
                to="/upload"
                class="inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-dark"
              >
                <Upload class="h-4 w-4" />
                Upload Documents
              </RouterLink>
              <RouterLink
                to="/chat"
                class="inline-flex items-center gap-2 rounded-xl border border-brand bg-white px-5 py-3 text-sm font-semibold text-brand hover:bg-blue-50"
              >
                <MessageSquare class="h-4 w-4" />
                Chat with AI
              </RouterLink>
            </div>
          </div>

          <img
            class="mx-auto hidden w-full max-w-md object-contain lg:block"
            src="/images/career-insights-flow.png"
            alt="Resume and job description flowing into career insights"
          />
        </div>
      </section>

      <section class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <RouterLink
          to="/upload"
          class="group rounded-2xl border border-blue-100 bg-[#eef5ff] p-5 transition hover:-translate-y-0.5 hover:shadow-md"
        >
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-brand shadow-sm">
            <Upload class="h-5 w-5" />
          </span>
          <p class="mt-4 text-[15px] font-bold text-slate-800">Upload Documents</p>
          <p class="mt-1 text-[13px] leading-relaxed text-slate-500">Add your resume and job descriptions</p>
          <ArrowRight class="mt-4 h-4 w-4 text-brand transition group-hover:translate-x-0.5" />
        </RouterLink>

        <RouterLink
          to="/chat"
          class="group rounded-2xl border border-emerald-100 bg-[#eefbf4] p-5 transition hover:-translate-y-0.5 hover:shadow-md"
        >
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-emerald-600 shadow-sm">
            <MessageSquare class="h-5 w-5" />
          </span>
          <p class="mt-4 text-[15px] font-bold text-slate-800">Chat with AI</p>
          <p class="mt-1 text-[13px] leading-relaxed text-slate-500">Ask questions about your career data</p>
          <ArrowRight class="mt-4 h-4 w-4 text-emerald-600 transition group-hover:translate-x-0.5" />
        </RouterLink>

        <RouterLink
          to="/analysis"
          class="group rounded-2xl border border-violet-100 bg-[#f4f0ff] p-5 transition hover:-translate-y-0.5 hover:shadow-md"
        >
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-violet-600 shadow-sm">
            <BarChart3 class="h-5 w-5" />
          </span>
          <p class="mt-4 text-[15px] font-bold text-slate-800">Analysis & Insights</p>
          <p class="mt-1 text-[13px] leading-relaxed text-slate-500">See skill gaps and match scores</p>
          <span class="mt-3 inline-block rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-amber-600">
            Coming soon
          </span>
        </RouterLink>

        <RouterLink
          to="/interview"
          class="group rounded-2xl border border-orange-100 bg-[#fff4ec] p-5 transition hover:-translate-y-0.5 hover:shadow-md"
        >
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-orange-500 shadow-sm">
            <Lightbulb class="h-5 w-5" />
          </span>
          <p class="mt-4 text-[15px] font-bold text-slate-800">Prepare for Interviews</p>
          <p class="mt-1 text-[13px] leading-relaxed text-slate-500">Get tailored questions and talking points</p>
          <ArrowRight class="mt-4 h-4 w-4 text-orange-500 transition group-hover:translate-x-0.5" />
        </RouterLink>
      </section>

      <p v-if="error" class="mt-6 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
        {{ error }}
        <button class="ml-2 font-semibold underline" type="button" @click="loadHome">Retry</button>
      </p>

      <section class="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-base font-bold text-slate-800">Recent Documents</h2>
            <RouterLink to="/documents" class="text-sm font-semibold text-brand hover:underline">View all</RouterLink>
          </div>
          <p v-if="loading" class="flex items-center gap-2 text-sm text-slate-400">
            <LoaderCircle class="h-4 w-4 animate-spin" />
            Loading documents…
          </p>
          <p v-else-if="!documents.length" class="text-sm text-slate-400">
            No documents yet.
            <RouterLink to="/upload" class="font-semibold text-brand hover:underline">Upload one</RouterLink>
            to get started.
          </p>
          <ul v-else class="divide-y divide-slate-100">
            <li v-for="doc in documents" :key="doc.id" class="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
              <span
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                :class="doc.doc_type === 'job' ? 'bg-blue-50 text-brand' : 'bg-red-50 text-red-500'"
              >
                <FileText class="h-5 w-5" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-semibold text-slate-800">{{ doc.filename }}</p>
                <p class="text-[12px] text-slate-400">
                  {{ kindLabel(doc) }} • {{ uploadedLabel(doc) }}
                </p>
              </div>
              <span
                v-if="doc.status === 'processed'"
                class="rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-600"
              >
                Processed
              </span>
              <span
                v-else-if="doc.status === 'failed'"
                class="rounded-full bg-red-50 px-2.5 py-1 text-[11px] font-semibold text-red-600"
              >
                Failed
              </span>
              <span
                v-else
                class="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-brand"
              >
                <LoaderCircle class="h-3 w-3 animate-spin" />
                Processing
              </span>
            </li>
          </ul>
        </div>

        <div class="flex flex-col gap-6">
          <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
            <h2 class="mb-4 text-base font-bold text-slate-800">Your Career at a Glance</h2>
            <div class="grid grid-cols-2 gap-3">
              <div class="rounded-xl bg-blue-50 p-3">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-brand">
                  <FileText class="h-4 w-4" />
                </span>
                <p class="mt-3 text-xl font-extrabold text-slate-800">{{ loading ? '—' : stats.resume_count }}</p>
                <p class="text-[12px] font-medium text-slate-500">Resume</p>
              </div>
              <div class="rounded-xl bg-[#eef2ff] p-3">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-indigo-700">
                  <Briefcase class="h-4 w-4" />
                </span>
                <p class="mt-3 text-xl font-extrabold text-slate-800">{{ loading ? '—' : stats.job_count }}</p>
                <p class="text-[12px] font-medium text-slate-500">Job Descriptions</p>
              </div>
              <div class="rounded-xl bg-violet-50 p-3">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-violet-600">
                  <BarChart3 class="h-4 w-4" />
                </span>
                <p class="mt-3 text-xl font-extrabold text-slate-800">{{ loading ? '—' : stats.insight_count }}</p>
                <p class="text-[12px] font-medium text-slate-500">AI Insights</p>
              </div>
              <div class="rounded-xl bg-orange-50 p-3">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-orange-500">
                  <Bookmark class="h-4 w-4" />
                </span>
                <p class="mt-3 text-xl font-extrabold text-slate-800">{{ loading ? '—' : stats.saved_result_count }}</p>
                <p class="text-[12px] font-medium text-slate-500">Saved Results</p>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-base font-bold text-slate-800">Recent Conversations</h2>
              <RouterLink to="/chat" class="text-sm font-semibold text-brand hover:underline">View all</RouterLink>
            </div>
            <p v-if="loading" class="flex items-center gap-2 text-sm text-slate-400">
              <LoaderCircle class="h-4 w-4 animate-spin" />
              Loading conversations…
            </p>
            <p v-else-if="!conversations.length" class="text-sm text-slate-400">
              No conversations yet.
              <RouterLink to="/chat" class="font-semibold text-brand hover:underline">Start chatting</RouterLink>
            </p>
            <ul v-else class="space-y-1">
              <li v-for="chat in conversations" :key="chat.id">
                <RouterLink
                  :to="{ path: '/chat', query: { conversation: chat.id } }"
                  class="flex items-start gap-3 rounded-xl px-1 py-2 hover:bg-slate-50"
                >
                  <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-brand">
                    <MessageSquare class="h-4 w-4" />
                  </span>
                  <span class="min-w-0">
                    <p class="truncate text-[13px] font-medium text-slate-700">{{ chat.title }}</p>
                    <p class="text-[11px] text-slate-400">{{ formatRelativeTime(chat.updated_at) }}</p>
                  </span>
                </RouterLink>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  </DashboardLayout>
</template>
