<script setup lang="ts">
import { BarChart3 } from '@lucide/vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
</script>

<template>
  <DashboardLayout>
    <div class="flex h-full items-center justify-center p-6">
      <div class="max-w-md rounded-2xl border border-slate-100 bg-white px-8 py-10 text-center shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
        <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-violet-600">
          <BarChart3 class="h-6 w-6" />
        </span>
        <p class="mt-4 text-[11px] font-bold tracking-[0.16em] text-violet-500 uppercase">Coming soon</p>
        <h1 class="mt-2 text-xl font-extrabold text-slate-800">Analysis & Insights</h1>
        <p class="mt-3 text-sm leading-relaxed text-slate-500">
          Skill-gap scores, match analysis, and personalized recommendations will appear here after
          documents are processed.
        </p>
      </div>
    </div>
  </DashboardLayout>
</template>
