<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Briefcase } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const { isAuthenticated } = useAuth()
const isPrivacy = computed(() => route.name === 'privacy')

const title = computed(() => (isPrivacy.value ? 'Privacy Policy' : 'Terms of Service'))
const updated = 'September 6, 2026'
const homeTo = computed(() => (isAuthenticated.value ? '/home' : '/'))
const backLabel = computed(() => (isAuthenticated.value ? 'Back to Home' : 'Back to sign up'))
</script>

<template>
  <div class="min-h-dvh bg-[#f7f8fb]">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-3xl items-center justify-between px-5 py-4">
        <RouterLink class="flex items-center gap-2 font-semibold text-slate-800" :to="homeTo">
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-white">
            <Briefcase class="h-4 w-4" />
          </span>
          Career Intelligence
        </RouterLink>
        <RouterLink class="text-sm font-medium text-brand hover:underline" :to="homeTo">{{ backLabel }}</RouterLink>
      </div>
    </header>

    <main class="mx-auto max-w-3xl px-5 py-10">
      <p class="text-[11px] font-bold tracking-[0.16em] text-brand uppercase">Legal</p>
      <h1 class="mt-2 text-3xl font-extrabold tracking-tight text-slate-900">{{ title }}</h1>
      <p class="mt-2 text-sm text-slate-400">Last updated {{ updated }}</p>

      <article
        class="mt-8 space-y-6 rounded-2xl border border-slate-100 bg-white p-6 text-sm leading-relaxed text-slate-600 shadow-[0_8px_24px_rgba(15,23,42,0.04)] sm:p-8"
      >
        <template v-if="isPrivacy">
          <p>
            This Privacy Policy explains how Career Intelligence handles information you provide when you create an
            account and use the product. It is a simple product summary, not legal advice.
          </p>
          <section>
            <h2 class="text-base font-semibold text-slate-900">What we collect</h2>
            <ul class="mt-2 list-disc space-y-1 pl-5">
              <li>Account details: name, email, and a hashed password.</li>
              <li>Documents you upload, such as resumes and job descriptions, plus pasted job text.</li>
              <li>Chat and interview messages, document processing status, and usage counts (for example token usage).</li>
            </ul>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">How we use it</h2>
            <p class="mt-2">
              We use this information to sign you in, index your documents, answer questions about your resume and
              jobs, prepare interview topics, and show usage. We do not sell your personal information.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Who can see it</h2>
            <p class="mt-2">
              Your documents and conversations belong to your account. We may send content to third-party AI providers
              so the product can extract skills, generate answers, and run interview practice. Do not upload
              information you are not allowed to share.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">How long we keep it</h2>
            <p class="mt-2">
              We keep account data, documents, and conversations until you delete them or close your account. You can
              delete individual documents from My Documents. Signing out does not delete your data.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Cookies and storage</h2>
            <p class="mt-2">
              The app stores a session token in your browser (localStorage if you choose Remember me, otherwise
              sessionStorage). Sidebar preferences may also be saved locally on your device.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Contact</h2>
            <p class="mt-2">
              Questions about this policy can be sent through the product’s Help &amp; Support contacts when they
              become available. Until then, use the email on your account record.
            </p>
          </section>
        </template>

        <template v-else>
          <p>
            These Terms of Service are a simple agreement for using Career Intelligence. By creating an account and
            checking the box on the sign-up form, you agree to these terms.
          </p>
          <section>
            <h2 class="text-base font-semibold text-slate-900">The service</h2>
            <p class="mt-2">
              Career Intelligence helps you upload resumes and job descriptions, review extracted skills, chat about
              your career data, and practice interviews. Features may change as the product grows. The service is
              provided as-is, without a guarantee of uninterrupted access or perfect AI output.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Your account</h2>
            <p class="mt-2">
              You must provide accurate account details and keep your password private. You are responsible for
              activity on your account. We may suspend access if we believe the service is being misused.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Your content</h2>
            <p class="mt-2">
              You keep ownership of resumes, job descriptions, and messages you submit. You grant us permission to
              store and process that content so the product can index files, generate answers, and show insights. You
              confirm you have the right to upload the material.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Acceptable use</h2>
            <p class="mt-2">
              Do not use the service to break the law, upload malware, attempt to access other people’s accounts, or
              submit content you do not have rights to. AI answers can be wrong; review them before you rely on them
              for applications or interviews.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Privacy</h2>
            <p class="mt-2">
              How we handle personal data is described in our
              <RouterLink class="font-medium text-brand hover:underline" to="/privacy">Privacy Policy</RouterLink>.
            </p>
          </section>
          <section>
            <h2 class="text-base font-semibold text-slate-900">Changes</h2>
            <p class="mt-2">
              We may update these terms. The “Last updated” date at the top will change when we do. Continued use of
              the service after an update means you accept the revised terms.
            </p>
          </section>
        </template>
      </article>
    </main>
  </div>
</template>
