<script setup lang="ts">
import { ref } from 'vue'
import { ArrowRight, Briefcase, CircleAlert, FileText } from '@lucide/vue'
import type { UploadedDoc } from '@/types/upload'
import { toUploadedDoc } from '@/types/upload'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopBar from '@/components/layout/AppTopBar.vue'
import DropZone from '@/components/upload/DropZone.vue'
import UploadedFileRow from '@/components/upload/UploadedFileRow.vue'
import UploadInfoSidebar from '@/components/upload/UploadInfoSidebar.vue'

type JobTab = 'files' | 'paste'

const resumeFiles = ref<UploadedDoc[]>([
  {
    id: 'resume-1',
    name: 'software-engineer-resume.pdf',
    sizeLabel: '245 KB',
    uploadedLabel: 'Uploaded just now',
    status: 'uploaded',
  },
])

const jobFiles = ref<UploadedDoc[]>([
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
    status: 'uploaded',
  },
  {
    id: 'job-3',
    name: 'GenAI Platform Engineer - InnovateAI.pdf',
    sizeLabel: '276 KB',
    uploadedLabel: 'Uploaded 4 minutes ago',
    status: 'uploaded',
  },
])

const jobTab = ref<JobTab>('files')
const pastedText = ref('')

function setResume(files: File[]) {
  const next = files[0]
  if (!next) return
  resumeFiles.value = [toUploadedDoc(next)]
}

function addJobs(files: File[]) {
  jobFiles.value = [...jobFiles.value, ...files.map(toUploadedDoc)]
}

function addPastedJob() {
  const text = pastedText.value.trim()
  if (!text) return
  const firstLine = text.split('\n')[0]?.slice(0, 48) || 'Pasted job description'
  jobFiles.value = [
    ...jobFiles.value,
    {
      id: `paste-${Date.now()}`,
      name: `${firstLine}.txt`,
      sizeLabel: `${Math.max(1, Math.round(text.length / 1024))} KB`,
      uploadedLabel: 'Uploaded just now',
      status: 'uploaded',
    },
  ]
  pastedText.value = ''
}
</script>

<template>
  <div class="flex h-dvh overflow-hidden bg-[#f5f7fb]">
    <AppSidebar />

    <div class="flex min-h-0 min-w-0 flex-1 flex-col">
      <AppTopBar />

      <div id="upload-scroll" class="min-h-0 flex-1 overflow-y-auto">
        <div class="flex items-start gap-6 p-6 xl:p-8">
        <main class="min-w-0 flex-1">
          <p class="text-[11px] font-semibold tracking-[0.16em] text-slate-400">UPLOAD DOCUMENTS</p>
          <h1 class="mt-2 text-[1.85rem] font-extrabold tracking-tight text-slate-900">
            Add Your Resume and Job Descriptions
          </h1>
          <p class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
            Upload your resume and one or more job descriptions to get AI-powered insights, skill gap analysis, and
            personalized recommendations.
          </p>

          <section class="mt-8">
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="flex items-center gap-2">
                  <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
                    <FileText class="h-4 w-4" />
                  </span>
                  <h2 class="text-base font-semibold text-slate-900">1. Upload Your Resume</h2>
                </div>
                <p class="mt-1 ml-10 text-xs text-slate-400">Supported formats: PDF, DOCX, TXT (Max 10 MB)</p>
              </div>
              <a class="inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline" href="#">
                <FileText class="h-3.5 w-3.5" />
                View sample
              </a>
            </div>

            <div class="mt-4">
              <DropZone
                button-label="Choose File"
                title="Drag and drop your resume here or click to browse files"
                hint="Supports PDF, DOCX, TXT (Max 10 MB)"
                @files="setResume"
              />
            </div>
            <ul v-if="resumeFiles.length" class="mt-3 space-y-2">
              <UploadedFileRow
                v-for="(file, index) in resumeFiles"
                :key="file.id"
                :file="file"
                @remove="resumeFiles.splice(index, 1)"
              />
            </ul>
          </section>

          <section class="mt-10">
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="flex items-center gap-2">
                  <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
                    <Briefcase class="h-4 w-4" />
                  </span>
                  <h2 class="text-base font-semibold text-slate-900">2. Add Job Descriptions</h2>
                </div>
                <p class="mt-1 ml-10 text-xs text-slate-400">
                  You can upload multiple job descriptions or paste the text directly.
                </p>
              </div>
              <a class="inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline" href="#">
                <FileText class="h-3.5 w-3.5" />
                View sample
              </a>
            </div>

            <div class="mt-4 flex gap-6 border-b border-slate-200 text-sm font-medium">
              <button
                class="pb-2.5"
                type="button"
                :class="jobTab === 'files' ? 'border-b-2 border-brand text-brand' : 'text-slate-400'"
                @click="jobTab = 'files'"
              >
                Upload Files
              </button>
              <button
                class="pb-2.5"
                type="button"
                :class="jobTab === 'paste' ? 'border-b-2 border-brand text-brand' : 'text-slate-400'"
                @click="jobTab = 'paste'"
              >
                Paste Text
              </button>
            </div>

            <div class="mt-4">
              <DropZone
                v-if="jobTab === 'files'"
                multiple
                button-label="Choose Files"
                title="Drag and drop job description files here or click to browse files"
                hint="Supports PDF, DOCX, TXT (Max 10 MB each)"
                @files="addJobs"
              />
              <div v-else class="rounded-2xl border border-slate-200 bg-white p-4">
                <textarea
                  v-model="pastedText"
                  class="h-36 w-full resize-y rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-brand/15"
                  placeholder="Paste a job description here…"
                />
                <button
                  class="mt-3 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
                  type="button"
                  @click="addPastedJob"
                >
                  Add job description
                </button>
              </div>
            </div>

            <ul v-if="jobFiles.length" class="mt-3 space-y-2">
              <UploadedFileRow
                v-for="(file, index) in jobFiles"
                :key="file.id"
                :file="file"
                @remove="jobFiles.splice(index, 1)"
              />
            </ul>
          </section>

          <footer class="mt-10 flex flex-wrap items-center justify-between gap-4 pb-6">
            <a class="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline" href="#">
              <CircleAlert class="h-4 w-4" />
              Need help? Check our document guidelines
            </a>
            <button
              class="inline-flex items-center gap-2 rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-dark"
              type="button"
            >
              Continue
              <ArrowRight class="h-4 w-4" />
            </button>
          </footer>
        </main>

        <UploadInfoSidebar />
        </div>
      </div>
    </div>
  </div>
</template>
