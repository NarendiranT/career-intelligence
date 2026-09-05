<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Briefcase, CircleAlert, FileText, LoaderCircle } from '@lucide/vue'
import { uploadDocument } from '@/api/documents'
import { showToast } from '@/composables/useToast'
import type { UploadedDoc } from '@/types/upload'
import { toUploadedDoc } from '@/types/upload'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import DropZone from '@/components/upload/DropZone.vue'
import SampleDocumentModal from '@/components/upload/SampleDocumentModal.vue'
import UploadedFileRow from '@/components/upload/UploadedFileRow.vue'
import UploadInfoSidebar from '@/components/upload/UploadInfoSidebar.vue'

type JobTab = 'files' | 'paste'
type SampleKind = 'resume' | 'job'

const SAMPLE_RESUME_PDF = '/samples/sample-resume.pdf'
const SAMPLE_JOB_PDF = '/samples/sample-job-description.pdf'

const router = useRouter()
const resumeFiles = ref<UploadedDoc[]>([])
const jobFiles = ref<UploadedDoc[]>([])
const sampleKind = ref<SampleKind | null>(null)
const submitting = ref(false)
const submitError = ref('')

const sampleOpen = computed(() => sampleKind.value !== null)
const sampleTitle = computed(() =>
  sampleKind.value === 'job' ? 'Sample job description' : 'Sample resume',
)
const sampleSrc = computed(() =>
  sampleKind.value === 'job' ? SAMPLE_JOB_PDF : SAMPLE_RESUME_PDF,
)

const jobTab = ref<JobTab>('files')
const pastedText = ref('')
const pendingCount = computed(() => resumeFiles.value.length + jobFiles.value.length)
const canContinue = computed(() => pendingCount.value > 0 && !submitting.value)

function addResumes(files: File[]) {
  resumeFiles.value = [...resumeFiles.value, ...files.map(toUploadedDoc)]
}

function addJobs(files: File[]) {
  jobFiles.value = [...jobFiles.value, ...files.map(toUploadedDoc)]
}

function addPastedJob() {
  const text = pastedText.value.trim()
  if (!text) return
  const firstLine = text.split('\n')[0]?.replace(/[/\\]/g, '-').slice(0, 48) || 'Pasted job description'
  const file = new File([text], `${firstLine}.txt`, { type: 'text/plain' })
  jobFiles.value = [...jobFiles.value, toUploadedDoc(file)]
  pastedText.value = ''
}

async function continueUpload() {
  if (!canContinue.value) return
  submitting.value = true
  submitError.value = ''
  const jobs = [
    ...resumeFiles.value.map((doc) => ({ file: doc.file, docType: 'resume' as const })),
    ...jobFiles.value.map((doc) => ({ file: doc.file, docType: 'job' as const })),
  ]
  const results = await Promise.allSettled(
    jobs.map((job) => uploadDocument(job.file, job.docType)),
  )
  const failed = results.filter((result) => result.status === 'rejected').length
  const uploaded = results.length - failed
  submitting.value = false
  if (uploaded === 0) {
    submitError.value = 'None of the files could be uploaded. Please try again.'
    return
  }
  if (failed > 0) {
    showToast(`${failed} file${failed === 1 ? '' : 's'} failed to upload.`, 'error')
  }
  await router.push('/documents')
}
</script>

<template>
  <DashboardLayout>
    <div id="upload-scroll" class="h-full overflow-y-auto p-6 xl:p-8">
        <main class="min-w-0">
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
                <p class="mt-1 ml-10 text-xs text-slate-400">Supported formats: PDF, DOCX, TXT (Max 10 MB each)</p>
              </div>
              <button
                class="inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline"
                type="button"
                @click="sampleKind = 'resume'"
              >
                <FileText class="h-3.5 w-3.5" />
                View sample
              </button>
            </div>

            <div class="mt-4">
              <DropZone
                multiple
                button-label="Choose Files"
                title="Drag and drop resume files here or click to browse files"
                hint="Supports PDF, DOCX, TXT (Max 10 MB each)"
                @files="addResumes"
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
              <button
                class="inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline"
                type="button"
                @click="sampleKind = 'job'"
              >
                <FileText class="h-3.5 w-3.5" />
                View sample
              </button>
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
            <div class="flex flex-col items-end gap-2">
              <p v-if="submitError" class="text-sm text-red-600">{{ submitError }}</p>
              <button
                class="inline-flex items-center gap-2 rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
                :disabled="!canContinue"
                @click="continueUpload"
              >
                <LoaderCircle v-if="submitting" class="h-4 w-4 animate-spin" />
                <template v-if="submitting">Uploading {{ pendingCount }} file{{ pendingCount === 1 ? '' : 's' }}…</template>
                <template v-else>
                  Continue
                  <ArrowRight class="h-4 w-4" />
                </template>
              </button>
            </div>
          </footer>
        </main>
    </div>

    <template #right>
      <UploadInfoSidebar />
    </template>
  </DashboardLayout>

  <SampleDocumentModal
    :open="sampleOpen"
    :title="sampleTitle"
    :src="sampleSrc"
    @close="sampleKind = null"
  />
</template>
