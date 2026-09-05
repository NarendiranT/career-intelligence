<script setup lang="ts">
import { Check, ChevronRight, Lightbulb, Shield, Target } from '@lucide/vue'

const tips = [
  'Use the most recent version of your resume',
  'Include multiple job descriptions to compare',
  'Prefer PDF when possible for cleaner parsing',
  'Paste the full posting, not just the title',
  'Keep files under 10 MB each',
]

const nextSteps = [
  'We extract and analyze the content using AI.',
  'We identify key skills, experience, and requirements.',
  'You can ask questions and get personalized insights.',
  'Compare your profile against multiple roles.',
]
</script>

<template>
  <aside class="flex h-full w-[300px] shrink-0 flex-col space-y-4 overflow-y-auto bg-white p-4">
    <section class="overflow-hidden rounded-2xl border border-amber-100 bg-white shadow-sm">
      <header class="flex items-center justify-between bg-amber-50 px-4 py-3">
        <div class="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-100 text-amber-600">
            <Lightbulb class="h-4 w-4" />
          </span>
          Tips for better results
        </div>
      </header>
      <ul class="space-y-2.5 px-4 py-3.5">
        <li v-for="tip in tips" :key="tip" class="flex items-start gap-2 text-[13px] leading-snug text-slate-600">
          <Check class="mt-0.5 h-4 w-4 shrink-0 text-brand" />
          {{ tip }}
        </li>
      </ul>
    </section>

    <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex items-center gap-2 text-sm font-semibold text-slate-800">
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
          <Target class="h-4 w-4" />
        </span>
        What happens next?
      </div>
      <ol class="mt-4 space-y-3">
        <li v-for="(step, index) in nextSteps" :key="step" class="flex items-start gap-3 text-[13px] leading-snug text-slate-600">
          <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500">
            {{ index + 1 }}
          </span>
          {{ step }}
        </li>
      </ol>
    </section>

    <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex items-center gap-2 text-sm font-semibold text-slate-800">
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
          <Shield class="h-4 w-4" />
        </span>
        Your data is secure
      </div>
      <p class="mt-3 text-[13px] leading-relaxed text-slate-500">
        All documents are encrypted and stored securely. We do not share your data with third parties.
      </p>
      <a class="mt-3 inline-flex items-center gap-1 text-[13px] font-medium text-brand hover:underline" href="#">
        Learn more about our privacy policy
        <ChevronRight class="h-3.5 w-3.5" />
      </a>
    </section>
  </aside>
</template>
