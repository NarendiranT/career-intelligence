<script setup lang="ts">
import { Briefcase, FileText, Lightbulb, Sparkles, Star } from '@lucide/vue'
import type { SkillActivity } from '@/types/skills'
import { PROFICIENCY_LEGEND } from '@/types/skills'
import { formatRelativeTime } from '@/utils/time'

defineProps<{
  insights: string[]
  recentActivity: SkillActivity[]
}>()

function activityIcon(kind: string) {
  if (kind === 'job_uploaded') return Briefcase
  if (kind === 'analysis_completed') return Sparkles
  return FileText
}
</script>

<template>
  <aside class="flex h-full w-[300px] shrink-0 flex-col space-y-4 overflow-y-auto bg-white p-4">
    <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <h2 class="text-sm font-bold text-slate-800">Skill Proficiency Legend</h2>
      <ul class="mt-3 space-y-2">
        <li v-for="row in PROFICIENCY_LEGEND" :key="row.stars" class="flex items-center justify-between">
          <span class="flex items-center gap-0.5">
            <Star
              v-for="n in 5"
              :key="n"
              class="h-3.5 w-3.5"
              :class="n <= row.stars ? 'fill-amber-400 text-amber-400' : 'text-slate-200'"
            />
          </span>
          <span class="text-xs font-medium text-slate-500">{{ row.label }}</span>
        </li>
      </ul>
    </section>

    <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex items-center gap-2">
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
          <Lightbulb class="h-4 w-4" />
        </span>
        <h2 class="text-sm font-bold text-slate-800">Key Insights</h2>
      </div>
      <ul v-if="insights.length" class="mt-3 list-disc space-y-1.5 pl-5 text-[13px] leading-relaxed text-slate-600">
        <li v-for="item in insights" :key="item">{{ item }}</li>
      </ul>
      <p v-else class="mt-3 text-[13px] text-slate-400">Insights appear after a resume is processed.</p>
    </section>

    <section class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <h2 class="text-sm font-bold text-slate-800">Recent Activity</h2>
      <ol v-if="recentActivity.length" class="mt-3 space-y-3">
        <li v-for="(item, index) in recentActivity" :key="`${item.kind}-${index}`" class="flex gap-3">
          <span
            class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-50 text-brand"
          >
            <component :is="activityIcon(item.kind)" class="h-3.5 w-3.5" />
          </span>
          <span class="min-w-0">
            <p class="text-[13px] font-semibold text-slate-800">{{ item.label }}</p>
            <p v-if="item.detail" class="truncate text-[12px] text-slate-500">{{ item.detail }}</p>
            <p class="text-[11px] text-slate-400">{{ formatRelativeTime(item.created_at) }}</p>
          </span>
        </li>
      </ol>
      <p v-else class="mt-3 text-[13px] text-slate-400">No document activity yet.</p>
    </section>
  </aside>
</template>
