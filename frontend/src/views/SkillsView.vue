<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Cloud,
  Code,
  Database,
  Layers,
  LoaderCircle,
  Sparkles,
  Star,
  Trophy,
  Upload,
} from '@lucide/vue'
import { fetchSkillsSummary } from '@/api/skills'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import SkillsRightPanel from '@/components/skills/SkillsRightPanel.vue'
import type { SkillCategory, SkillsSummary } from '@/types/skills'

const SKILL_PREVIEW_LIMIT = 10

const CATEGORY_ICONS = {
  'Programming Languages': Code,
  'Frameworks & Libraries': Layers,
  'Cloud & DevOps': Cloud,
  'AI / Machine Learning': Sparkles,
  'Databases & Storage': Database,
  'Other Skills': Sparkles,
} as const

const emptySummary: SkillsSummary = {
  resume_count: 0,
  total_skills: 0,
  skill_summary: '',
  insights: [],
  categories: [],
  recent_activity: [],
}

const loading = ref(true)
const error = ref('')
const summary = ref<SkillsSummary>({ ...emptySummary })
const expandedCategories = ref<Record<string, boolean>>({})
const hasSkills = computed(() => summary.value.total_skills > 0)

function categoryIcon(name: string) {
  return CATEGORY_ICONS[name as keyof typeof CATEGORY_ICONS] ?? Sparkles
}

function isExpanded(name: string): boolean {
  return Boolean(expandedCategories.value[name])
}

function visibleSkills(category: SkillCategory) {
  if (isExpanded(category.name) || category.skills.length <= SKILL_PREVIEW_LIMIT) {
    return category.skills
  }
  return category.skills.slice(0, SKILL_PREVIEW_LIMIT)
}

function toggleCategory(name: string) {
  expandedCategories.value = {
    ...expandedCategories.value,
    [name]: !expandedCategories.value[name],
  }
}

async function loadSkills(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    summary.value = await fetchSkillsSummary()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load skills.'
    summary.value = { ...emptySummary }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadSkills()
})
</script>

<template>
  <DashboardLayout>
    <div id="skills-scroll" class="h-full overflow-y-auto p-6">
      <div class="mx-auto flex max-w-5xl flex-col gap-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 class="text-2xl font-extrabold text-slate-800">My Skills</h1>
            <p class="mt-1 text-sm text-slate-500">
              Combined from every resume you have uploaded.
            </p>
          </div>
          <RouterLink
            to="/upload"
            class="inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-dark"
          >
            <Upload class="h-4 w-4" />
            Upload Resume
          </RouterLink>
        </div>

        <p v-if="error" class="rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-600">
          {{ error }}
        </p>

        <div v-if="loading" class="flex items-center gap-2 text-sm text-slate-500">
          <LoaderCircle class="h-4 w-4 animate-spin" />
          Loading skill profile…
        </div>

        <template v-else>
          <section
            class="flex flex-col gap-4 rounded-2xl border border-amber-100 bg-gradient-to-r from-amber-50 via-white to-white p-5 sm:flex-row sm:items-center sm:justify-between"
          >
            <div class="flex items-start gap-3">
              <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-amber-600">
                <Trophy class="h-6 w-6" />
              </span>
              <div>
                <p class="text-sm font-semibold text-slate-800">Overall Skill Profile</p>
                <p class="mt-1 max-w-xl text-sm leading-relaxed text-slate-600">
                  {{ summary.skill_summary }}
                </p>
              </div>
            </div>
            <div class="shrink-0 rounded-2xl bg-white px-5 py-3 text-center shadow-sm">
              <p class="text-[11px] font-semibold tracking-wide text-slate-400 uppercase">Total Skills</p>
              <p class="text-3xl font-extrabold text-slate-800">{{ summary.total_skills }}</p>
            </div>
          </section>

          <section
            v-if="!hasSkills"
            class="rounded-2xl border border-dashed border-slate-200 bg-white px-6 py-12 text-center"
          >
            <p class="text-sm font-semibold text-slate-800">No skills yet</p>
            <p class="mt-1 text-sm text-slate-500">
              Upload a resume so we can extract and combine your skills.
            </p>
            <RouterLink
              to="/upload"
              class="mt-4 inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              <Upload class="h-4 w-4" />
              Upload Resume
            </RouterLink>
          </section>

          <section v-else class="grid gap-4 md:grid-cols-2">
            <article
              v-for="category in summary.categories"
              :key="category.name"
              class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]"
            >
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2">
                  <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-brand">
                    <component :is="categoryIcon(category.name)" class="h-4 w-4" />
                  </span>
                  <h2 class="text-sm font-bold text-slate-800">{{ category.name }}</h2>
                </div>
                <span class="text-[11px] font-semibold text-slate-400">
                  {{ category.skills.length }}
                  {{ category.skills.length === 1 ? 'skill' : 'skills' }}
                </span>
              </div>
              <ul
                class="mt-4 space-y-3"
                :class="isExpanded(category.name) && category.skills.length > SKILL_PREVIEW_LIMIT ? 'max-h-[22rem] overflow-y-auto pr-1' : ''"
              >
                <li
                  v-for="skill in visibleSkills(category)"
                  :key="skill.name"
                  class="flex items-center justify-between gap-3"
                >
                  <span class="text-sm font-medium text-slate-700">{{ skill.name }}</span>
                  <span class="flex items-center gap-0.5" :aria-label="`${skill.proficiency} out of 5`">
                    <Star
                      v-for="n in 5"
                      :key="n"
                      class="h-3.5 w-3.5"
                      :class="n <= skill.proficiency ? 'fill-amber-400 text-amber-400' : 'text-slate-200'"
                    />
                  </span>
                </li>
              </ul>
              <button
                v-if="category.skills.length > SKILL_PREVIEW_LIMIT"
                class="mt-3 text-sm font-semibold text-brand hover:text-brand-dark"
                type="button"
                @click="toggleCategory(category.name)"
              >
                {{ isExpanded(category.name) ? 'View less' : `View more (${category.skills.length - SKILL_PREVIEW_LIMIT})` }}
              </button>
            </article>
          </section>

          <p
            class="rounded-2xl bg-violet-50 px-4 py-3 text-sm text-violet-800"
          >
            Keep your resume updated with new skills and projects to get a more accurate skill profile.
          </p>
        </template>
      </div>
    </div>

    <template #right>
      <SkillsRightPanel :insights="summary.insights" :recent-activity="summary.recent_activity" />
    </template>
  </DashboardLayout>
</template>
