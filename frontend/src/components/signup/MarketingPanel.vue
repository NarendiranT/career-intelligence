<script setup lang="ts">
import { BarChart3, Briefcase, FileText, Lightbulb, Rocket } from '@lucide/vue'
import FeatureItem from './FeatureItem.vue'
import CareerFlowIllustration from './CareerFlowIllustration.vue'

const features = [
  {
    title: 'Smarter Job Matching',
    description: 'Find the right roles for your skills and experience.',
    icon: FileText,
    tone: 'blue',
  },
  {
    title: 'Skill Gap Analysis',
    description: 'Identify missing skills and get learning recommendations.',
    icon: BarChart3,
    tone: 'purple',
  },
  {
    title: 'Interview Preparation',
    description: 'Get tailored questions and tips.',
    icon: Lightbulb,
    tone: 'green',
  },
  {
    title: 'Track Your Progress',
    description: 'Save insights and track your career growth.',
    icon: Rocket,
    tone: 'orange',
  },
] as const
</script>

<template>
  <section
    class="relative hidden overflow-hidden bg-linear-to-br from-[#e8f1ff] via-[#f3f8ff] to-white px-10 py-8 lg:flex lg:flex-col"
  >
    <div class="pointer-events-none absolute inset-x-0 bottom-0 h-48 bg-linear-to-t from-[#dbeafe]/70 to-transparent" />

    <header class="relative z-10 flex items-center gap-2.5">
      <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-white shadow-sm">
        <Briefcase class="h-5 w-5" :stroke-width="2.2" />
      </span>
      <span class="text-[17px] font-bold tracking-tight text-slate-800">Career Intelligence</span>
    </header>

    <div class="relative z-10 mt-10 max-w-xl">
      <p class="text-[11px] font-semibold tracking-[0.18em] text-sky-500">AI-POWERED CAREER ASSISTANT</p>
      <h1 class="mt-3 text-[2.35rem] leading-tight font-extrabold text-slate-900">
        Your Career Companion for
        <span class="text-brand">What’s Next</span>
      </h1>
      <p class="mt-4 max-w-md text-[15px] leading-relaxed text-slate-500">
        Upload your resume, add job descriptions, and get AI-powered insights, skill gap analysis, and
        personalized recommendations.
      </p>
    </div>

    <div class="relative z-10 mt-8 grid max-w-5xl flex-1 grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] items-center gap-8">
      <ul class="space-y-5">
        <FeatureItem
          v-for="feature in features"
          :key="feature.title"
          :title="feature.title"
          :description="feature.description"
          :icon="feature.icon"
          :tone="feature.tone"
        />
      </ul>
      <CareerFlowIllustration />
    </div>

    <footer class="relative z-10 mt-auto flex items-end justify-between pt-8 pb-2">
      <blockquote class="max-w-md">
        <p class="text-[13px] leading-relaxed text-slate-500 italic">
          “This tool gave me clarity on my strengths and helped me prepare for interviews effectively.”
        </p>
        <cite class="mt-2 block text-sm font-semibold not-italic text-slate-700">— Happy User</cite>
      </blockquote>
      <div class="flex gap-1.5 pb-1">
        <span class="h-1.5 w-5 rounded-full bg-brand" />
        <span class="h-1.5 w-1.5 rounded-full bg-sky-200" />
        <span class="h-1.5 w-1.5 rounded-full bg-sky-200" />
      </div>
    </footer>
  </section>
</template>
