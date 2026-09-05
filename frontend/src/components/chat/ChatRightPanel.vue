<script setup lang="ts">
import { computed } from 'vue'
import { Briefcase, ChevronRight, CircleAlert, FileText, Plus, Sparkles, X } from '@lucide/vue'
import { documentLibrary } from '@/types/chat'

const tab = defineModel<'documents' | 'settings'>('tab', { default: 'documents' })
const selectedResumeId = defineModel<string>('resumeId', { default: 'resume-1' })
const selectedJobIds = defineModel<string[]>('jobIds', { default: () => ['job-1', 'job-2'] })
const temperature = defineModel<number>('temperature', { default: 0.7 })
const topP = defineModel<number>('topP', { default: 1 })
const maxTokens = defineModel<number>('maxTokens', { default: 1024 })
const model = defineModel<string>('model', { default: 'deep-research' })
const stream = defineModel<boolean>('stream', { default: true })
const webSearch = defineModel<boolean>('webSearch', { default: false })
const systemPrompt = defineModel<string>('systemPrompt', {
  default: 'You are Career Intelligence, a helpful career coach. Use the selected resume and job descriptions to give specific, actionable advice.',
})

const resumes = documentLibrary.filter((doc) => doc.kind === 'resume')
const jobs = documentLibrary.filter((doc) => doc.kind === 'job')

const selectedResume = computed(() => resumes.find((doc) => doc.id === selectedResumeId.value))
const selectedJobs = computed(() => jobs.filter((doc) => selectedJobIds.value.includes(doc.id)))

const examples = [
  'How well do I match this role?',
  'What skills am I missing?',
  'Give me interview preparation tips',
  'Rewrite my resume summary for this job',
]

defineEmits<{
  ask: [question: string]
}>()

function toggleJob(id: string) {
  const current = selectedJobIds.value
  selectedJobIds.value = current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
}

function removeJob(id: string) {
  selectedJobIds.value = selectedJobIds.value.filter((item) => item !== id)
}
</script>

<template>
  <aside class="flex h-full w-[320px] shrink-0 flex-col overflow-y-auto bg-white p-4">
    <div class="rounded-xl bg-violet-50 px-3 py-2.5">
      <p class="flex items-center gap-1.5 text-xs font-semibold text-violet-700">
        <Sparkles class="h-3.5 w-3.5" />
        Powered by AI
      </p>
      <p class="mt-1 text-[11px] leading-relaxed text-violet-700/80">
        Answers use only the resume and job descriptions you select here.
      </p>
    </div>

    <div class="mt-4 flex border-b border-slate-200 text-sm font-medium">
      <button
        class="flex-1 pb-2"
        type="button"
        :class="tab === 'documents' ? 'border-b-2 border-brand text-brand' : 'text-slate-400'"
        @click="tab = 'documents'"
      >
        Selected Documents
      </button>
      <button
        class="flex-1 pb-2"
        type="button"
        :class="tab === 'settings' ? 'border-b-2 border-brand text-brand' : 'text-slate-400'"
        @click="tab = 'settings'"
      >
        Chat Settings
      </button>
    </div>

    <div v-if="tab === 'documents'" class="mt-4 space-y-4">
      <section>
        <label class="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <FileText class="h-3.5 w-3.5 text-brand" />
          Select Resume
        </label>
        <select
          v-model="selectedResumeId"
          class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-brand"
        >
          <option v-for="resume in resumes" :key="resume.id" :value="resume.id">{{ resume.name }}</option>
        </select>
        <p v-if="selectedResume" class="mt-1.5 text-[11px] text-emerald-600">Processed • {{ selectedResume.sizeLabel }}</p>
      </section>

      <section>
        <label class="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <Briefcase class="h-3.5 w-3.5 text-brand" />
          Select Job Description(s)
        </label>
        <div class="mt-2 space-y-1.5">
          <label
            v-for="job in jobs"
            :key="job.id"
            class="flex items-start gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700"
          >
            <input
              class="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand"
              type="checkbox"
              :checked="selectedJobIds.includes(job.id)"
              @change="toggleJob(job.id)"
            />
            <span>
              {{ job.name }}
              <span class="block text-[11px] text-slate-400">{{ job.sizeLabel }}</span>
            </span>
          </label>
        </div>
      </section>

      <section>
        <p class="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
          Active Context
          <CircleAlert class="h-3.5 w-3.5 text-slate-400" />
        </p>
        <ul class="mt-2 space-y-2">
          <li
            v-if="selectedResume"
            class="flex items-start justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2"
          >
            <div>
              <p class="text-[11px] font-medium text-slate-400">Resume</p>
              <p class="text-[13px] font-medium text-slate-800">{{ selectedResume.name }}</p>
              <p class="text-[11px] text-emerald-600">Processed • {{ selectedResume.sizeLabel }}</p>
            </div>
          </li>
          <li
            v-for="job in selectedJobs"
            :key="job.id"
            class="flex items-start justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2"
          >
            <div>
              <p class="text-[11px] font-medium text-slate-400">Job Description</p>
              <p class="text-[13px] font-medium text-slate-800">{{ job.name }}</p>
              <p class="text-[11px] text-emerald-600">Processed • {{ job.sizeLabel }}</p>
            </div>
            <button class="text-slate-400 hover:text-slate-600" type="button" :aria-label="`Remove ${job.name}`" @click="removeJob(job.id)">
              <X class="h-4 w-4" />
            </button>
          </li>
        </ul>
        <p class="mt-2 text-[11px] text-slate-400">{{ selectedJobs.length }} job description{{ selectedJobs.length === 1 ? '' : 's' }} selected</p>
      </section>
    </div>

    <div v-else class="mt-4 space-y-4">
      <label class="block text-xs font-semibold text-slate-700">
        Model
        <select
          v-model="model"
          class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
        >
          <option value="deep-research">Deep Research</option>
          <option value="gpt-4o">GPT-4o</option>
          <option value="claude-3.5">Claude 3.5 Sonnet</option>
          <option value="gemini-pro">Gemini Pro</option>
        </select>
      </label>

      <label class="block text-xs font-semibold text-slate-700">
        Temperature
        <span class="ml-2 font-normal text-slate-400">{{ temperature.toFixed(1) }}</span>
        <input v-model.number="temperature" class="mt-2 w-full accent-brand" type="range" min="0" max="2" step="0.1" />
        <span class="mt-1 flex justify-between text-[11px] font-normal text-slate-400">
          <span>Focused</span>
          <span>Creative</span>
        </span>
      </label>

      <label class="block text-xs font-semibold text-slate-700">
        Top P
        <span class="ml-2 font-normal text-slate-400">{{ Number(topP).toFixed(2) }}</span>
        <input v-model.number="topP" class="mt-2 w-full accent-brand" type="range" min="0" max="1" step="0.05" />
      </label>

      <label class="block text-xs font-semibold text-slate-700">
        Max response tokens
        <span class="ml-2 font-normal text-slate-400">{{ maxTokens }}</span>
        <input v-model.number="maxTokens" class="mt-2 w-full accent-brand" type="range" min="256" max="4096" step="128" />
      </label>

      <label class="flex items-center justify-between text-xs font-semibold text-slate-700">
        Stream responses
        <input v-model="stream" class="h-4 w-4 rounded border-slate-300 text-brand" type="checkbox" />
      </label>

      <label class="flex items-center justify-between text-xs font-semibold text-slate-700">
        Web search
        <input v-model="webSearch" class="h-4 w-4 rounded border-slate-300 text-brand" type="checkbox" />
      </label>

      <label class="block text-xs font-semibold text-slate-700">
        System instructions
        <textarea
          v-model="systemPrompt"
          class="mt-2 h-28 w-full resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal text-slate-700 outline-none focus:border-brand"
        />
      </label>
    </div>

    <section class="mt-6">
      <p class="text-xs font-semibold text-slate-700">Example questions</p>
      <ul class="mt-2 space-y-1">
        <li v-for="example in examples" :key="example">
          <button
            class="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left text-[13px] text-slate-600 hover:bg-slate-50"
            type="button"
            @click="$emit('ask', example)"
          >
            {{ example }}
            <ChevronRight class="h-3.5 w-3.5 text-slate-400" />
          </button>
        </li>
      </ul>
    </section>

    <div class="mt-auto rounded-xl bg-violet-50 p-3">
      <p class="flex items-center gap-1.5 text-xs font-semibold text-violet-800">
        <Plus class="h-3.5 w-3.5" />
        Tip
      </p>
      <p class="mt-1 text-[12px] leading-relaxed text-violet-800/80">
        Select one resume and the jobs you care about, then ask for a match score, skill gaps, or interview questions.
      </p>
    </div>
  </aside>
</template>
