<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  BarElement,
  CategoryScale,
  Chart,
  DoughnutController,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
  ArcElement,
  BarController,
} from 'chart.js'
import { FileText, LoaderCircle, MessageSquare, Mic, TrendingUp } from '@lucide/vue'
import { fetchUsageSummary } from '@/api/usage'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import UsageActivitiesModal from '@/components/usage/UsageActivitiesModal.vue'
import type { UsageFeature, UsageFeatureId, UsageRange, UsageSummary } from '@/types/usage'

Chart.register(
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler,
  Tooltip,
  Legend,
  DoughnutController,
  ArcElement,
  BarController,
  BarElement,
)

const FEATURE_COLORS: Record<UsageFeatureId, string> = {
  chat: '#2563eb',
  interview: '#8b5cf6',
  documents: '#10b981',
}

const FEATURE_ICONS = {
  chat: MessageSquare,
  interview: Mic,
  documents: FileText,
} as const

const RANGE_OPTIONS: { value: UsageRange; label: string }[] = [
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: '90d', label: 'Last 90 Days' },
]

const emptySummary: UsageSummary = {
  range: '30d',
  days: 30,
  total_tokens: 0,
  prompt_tokens: 0,
  completion_tokens: 0,
  event_count: 0,
  range_tokens: 0,
  previous_range_tokens: 0,
  delta_percent: 0,
  by_event_type: [],
  features: [
    { id: 'chat', label: 'Chat with Assistant', tokens: 0, percent: 0, activity_count: 0 },
    { id: 'interview', label: 'Interview Preparation', tokens: 0, percent: 0, activity_count: 0 },
    { id: 'documents', label: 'Document Processing', tokens: 0, percent: 0, activity_count: 0 },
  ],
  daily: [],
  recent: [],
}

const range = ref<UsageRange>('30d')
const loading = ref(true)
const error = ref('')
const summary = ref<UsageSummary>({ ...emptySummary })
const allOpen = ref(false)
const filterStart = ref('')
const filterEnd = ref('')

const trendCanvas = ref<HTMLCanvasElement | null>(null)
const donutCanvas = ref<HTMLCanvasElement | null>(null)
const barsCanvas = ref<HTMLCanvasElement | null>(null)

let trendChart: Chart | null = null
let donutChart: Chart | null = null
let barsChart: Chart | null = null

const features = computed(() => {
  const byId = new Map(summary.value.features.map((row) => [row.id, row]))
  return emptySummary.features.map((fallback) => byId.get(fallback.id) ?? fallback)
})

const chatFeature = computed(() => features.value[0])
const interviewFeature = computed(() => features.value[1])
const documentsFeature = computed(() => features.value[2])

const recentRows = computed(() => summary.value.recent.slice(0, 5))

const rangeLabel = computed(
  () => RANGE_OPTIONS.find((item) => item.value === range.value)?.label ?? 'Last 30 Days',
)

function toDateInput(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function rangeBounds(days: number): { start: string; end: string } {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - (days - 1))
  return { start: toDateInput(start), end: toDateInput(end) }
}

function openAllUsage(): void {
  const bounds = rangeBounds(summary.value.days || 30)
  filterStart.value = bounds.start
  filterEnd.value = bounds.end
  allOpen.value = true
}

function formatTokens(value: number): string {
  return value.toLocaleString('en-US')
}

function formatDateTime(value: string): string {
  const stamp = new Date(value)
  if (Number.isNaN(stamp.getTime())) return value
  return stamp.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function featureMeta(id: UsageFeatureId): UsageFeature {
  return features.value.find((row) => row.id === id) ?? emptySummary.features.find((row) => row.id === id)!
}

function destroyCharts(): void {
  trendChart?.destroy()
  donutChart?.destroy()
  barsChart?.destroy()
  trendChart = null
  donutChart = null
  barsChart = null
}

function renderCharts(): void {
  destroyCharts()
  const data = summary.value
  const labels = data.daily.map((row) => {
    const stamp = new Date(`${row.date}T00:00:00`)
    return stamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  })

  if (trendCanvas.value) {
    trendChart = new Chart(trendCanvas.value, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Chat with Assistant',
            data: data.daily.map((row) => row.chat),
            borderColor: FEATURE_COLORS.chat,
            backgroundColor: 'rgba(37, 99, 235, 0.08)',
            fill: true,
            tension: 0.35,
            pointRadius: 2,
          },
          {
            label: 'Interview Preparation',
            data: data.daily.map((row) => row.interview),
            borderColor: FEATURE_COLORS.interview,
            backgroundColor: 'rgba(139, 92, 246, 0.08)',
            fill: true,
            tension: 0.35,
            pointRadius: 2,
          },
          {
            label: 'Document Processing',
            data: data.daily.map((row) => row.documents),
            borderColor: FEATURE_COLORS.documents,
            backgroundColor: 'rgba(16, 185, 129, 0.08)',
            fill: true,
            tension: 0.35,
            pointRadius: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8, color: '#94a3b8' } },
          y: { beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: '#f1f5f9' } },
        },
      },
    })
  }

  if (donutCanvas.value) {
    donutChart = new Chart(donutCanvas.value, {
      type: 'doughnut',
      data: {
        labels: features.value.map((row) => row.label),
        datasets: [
          {
            data: features.value.map((row) => row.tokens),
            backgroundColor: [FEATURE_COLORS.chat, FEATURE_COLORS.interview, FEATURE_COLORS.documents],
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: { legend: { display: false } },
      },
    })
  }

  if (barsCanvas.value) {
    barsChart = new Chart(barsCanvas.value, {
      type: 'bar',
      data: {
        labels: ['Chat with Assistant', 'Interview Preparation', 'Documents Uploaded'],
        datasets: [
          {
            data: [
              chatFeature.value.activity_count,
              interviewFeature.value.activity_count,
              documentsFeature.value.activity_count,
            ],
            backgroundColor: [FEATURE_COLORS.chat, FEATURE_COLORS.interview, FEATURE_COLORS.documents],
            borderRadius: 8,
            barThickness: 28,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748b' } },
          y: { beginAtZero: true, ticks: { precision: 0, color: '#94a3b8' }, grid: { color: '#f1f5f9' } },
        },
      },
    })
  }
}

async function loadUsage(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    summary.value = await fetchUsageSummary(range.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load usage.'
    summary.value = { ...emptySummary, range: range.value }
  } finally {
    loading.value = false
    await nextTick()
    renderCharts()
  }
}

onMounted(() => {
  void loadUsage()
})

watch(range, () => {
  void loadUsage()
})

onBeforeUnmount(() => {
  destroyCharts()
})
</script>

<template>
  <DashboardLayout>
    <div id="usage-scroll" class="h-full overflow-y-auto p-6">
      <div class="mx-auto flex max-w-6xl flex-col gap-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 class="text-2xl font-extrabold text-slate-800">Usage</h1>
            <p class="mt-1 text-sm text-slate-500">
              Track your AI usage, token consumption, and activity across all features.
            </p>
          </div>
          <label class="text-sm font-medium text-slate-500">
            <span class="sr-only">Date range</span>
            <select
              v-model="range"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 outline-none focus:border-brand focus:ring-2 focus:ring-brand/15"
            >
              <option v-for="option in RANGE_OPTIONS" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>

        <p v-if="error" class="rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-600">
          {{ error }}
        </p>

        <section class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <article class="rounded-2xl border border-slate-100 bg-white p-4 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-600">Chat with Assistant</p>
              <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-brand">
                <MessageSquare class="h-4 w-4" />
              </span>
            </div>
            <p class="mt-3 text-2xl font-extrabold text-slate-800">
              {{ loading ? '—' : formatTokens(chatFeature.tokens) }}
            </p>
            <p class="text-xs font-medium text-slate-400">Tokens Used</p>
            <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full bg-brand" :style="{ width: `${chatFeature.percent}%` }" />
            </div>
            <p class="mt-1 text-right text-[11px] font-semibold text-slate-400">{{ chatFeature.percent }}%</p>
          </article>

          <article class="rounded-2xl border border-slate-100 bg-white p-4 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-600">Interview Preparation</p>
              <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-50 text-violet-600">
                <Mic class="h-4 w-4" />
              </span>
            </div>
            <p class="mt-3 text-2xl font-extrabold text-slate-800">
              {{ loading ? '—' : formatTokens(interviewFeature.tokens) }}
            </p>
            <p class="text-xs font-medium text-slate-400">Tokens Used</p>
            <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full bg-violet-500" :style="{ width: `${interviewFeature.percent}%` }" />
            </div>
            <p class="mt-1 text-right text-[11px] font-semibold text-slate-400">{{ interviewFeature.percent }}%</p>
          </article>

          <article class="rounded-2xl border border-slate-100 bg-white p-4 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-600">Document Processing</p>
              <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                <FileText class="h-4 w-4" />
              </span>
            </div>
            <p class="mt-3 text-2xl font-extrabold text-slate-800">
              {{ loading ? '—' : formatTokens(documentsFeature.tokens) }}
            </p>
            <p class="text-xs font-medium text-slate-400">Tokens Used</p>
            <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${documentsFeature.percent}%` }" />
            </div>
            <p class="mt-1 text-right text-[11px] font-semibold text-slate-400">{{ documentsFeature.percent }}%</p>
          </article>

          <article class="rounded-2xl border border-slate-100 bg-white p-4 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-600">Total Tokens Used</p>
              <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-50 text-slate-600">
                <TrendingUp class="h-4 w-4" />
              </span>
            </div>
            <p class="mt-3 text-2xl font-extrabold text-slate-800">
              {{ loading ? '—' : formatTokens(summary.range_tokens) }}
            </p>
            <p class="text-xs font-medium text-slate-400">Across all features</p>
            <p
              class="mt-4 text-sm font-semibold"
              :class="summary.delta_percent >= 0 ? 'text-emerald-600' : 'text-red-500'"
            >
              {{ summary.delta_percent >= 0 ? '↑' : '↓' }}
              {{ Math.abs(summary.delta_percent) }}% vs previous {{ summary.days }} days
            </p>
          </article>
        </section>

        <section class="grid gap-4 lg:grid-cols-5">
          <article class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)] lg:col-span-3">
            <div class="mb-3 flex items-center justify-between">
              <div>
                <h2 class="text-base font-bold text-slate-800">Token Usage Trend</h2>
                <p class="text-xs text-slate-400">Daily token usage by feature.</p>
              </div>
              <p v-if="loading" class="flex items-center gap-1 text-xs text-slate-400">
                <LoaderCircle class="h-3.5 w-3.5 animate-spin" />
                Loading
              </p>
            </div>
            <div class="h-64">
              <canvas ref="trendCanvas" />
            </div>
          </article>

          <article class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)] lg:col-span-2">
            <h2 class="text-base font-bold text-slate-800">Token Usage by Feature</h2>
            <p class="text-xs text-slate-400">Share of {{ formatTokens(summary.range_tokens) }} tokens in {{ rangeLabel.toLowerCase() }}.</p>
            <div class="relative mx-auto mt-4 h-48 w-48">
              <canvas ref="donutCanvas" />
              <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <p class="text-xl font-extrabold text-slate-800">{{ formatTokens(summary.range_tokens) }}</p>
                <p class="text-[11px] font-medium text-slate-400">Total</p>
              </div>
            </div>
            <ul class="mt-4 space-y-2 text-sm">
              <li v-for="feature in features" :key="feature.id" class="flex items-center justify-between gap-2">
                <span class="flex items-center gap-2 text-slate-600">
                  <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: FEATURE_COLORS[feature.id] }" />
                  {{ feature.label }}
                </span>
                <span class="font-semibold text-slate-700">
                  {{ formatTokens(feature.tokens) }}
                  <span class="font-medium text-slate-400">({{ feature.percent }}%)</span>
                </span>
              </li>
            </ul>
          </article>
        </section>

        <section class="grid gap-4 lg:grid-cols-5">
          <article class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)] lg:col-span-2">
            <h2 class="text-base font-bold text-slate-800">Activity Count</h2>
            <p class="text-xs text-slate-400">Number of times each feature was used.</p>
            <div class="mt-4 h-56">
              <canvas ref="barsCanvas" />
            </div>
          </article>

          <article class="rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)] lg:col-span-3">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h2 class="text-base font-bold text-slate-800">Recent Usage</h2>
                <p class="text-xs text-slate-400">Your latest 5 activities across all features.</p>
              </div>
              <button
                class="shrink-0 text-sm font-semibold text-brand hover:text-brand-dark disabled:cursor-not-allowed disabled:text-slate-300"
                type="button"
                :disabled="loading"
                @click="openAllUsage"
              >
                View all
              </button>
            </div>
            <div v-if="!loading && recentRows.length === 0" class="mt-8 text-center text-sm text-slate-400">
              No usage in this date range yet.
            </div>
            <div v-else class="mt-3 overflow-x-auto">
              <table class="w-full min-w-[520px] text-left text-sm">
                <thead>
                  <tr class="border-b border-slate-100 text-[11px] font-semibold tracking-wide text-slate-400 uppercase">
                    <th class="py-2 pr-3 font-semibold">Date & Time</th>
                    <th class="py-2 pr-3 font-semibold">Feature</th>
                    <th class="py-2 pr-3 font-semibold">Tokens Used</th>
                    <th class="py-2 font-semibold">Details</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in recentRows" :key="row.id" class="border-b border-slate-50 last:border-0">
                    <td class="py-3 pr-3 whitespace-nowrap text-slate-500">{{ formatDateTime(row.created_at) }}</td>
                    <td class="py-3 pr-3">
                      <span class="inline-flex items-center gap-2 font-medium text-slate-700">
                        <span
                          class="flex h-7 w-7 items-center justify-center rounded-lg"
                          :style="{ backgroundColor: `${FEATURE_COLORS[row.feature]}14`, color: FEATURE_COLORS[row.feature] }"
                        >
                          <component :is="FEATURE_ICONS[row.feature]" class="h-3.5 w-3.5" />
                        </span>
                        {{ featureMeta(row.feature).label }}
                      </span>
                    </td>
                    <td class="py-3 pr-3 font-semibold text-slate-800">{{ formatTokens(row.tokens) }}</td>
                    <td class="py-3 text-slate-500">{{ row.details }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>
      </div>
    </div>
    <UsageActivitiesModal
      :open="allOpen"
      :start="filterStart"
      :end="filterEnd"
      :feature-meta="featureMeta"
      :feature-icons="FEATURE_ICONS"
      :format-date-time="formatDateTime"
      :format-tokens="formatTokens"
      @close="allOpen = false"
      @update:start="filterStart = $event"
      @update:end="filterEnd = $event"
    />
  </DashboardLayout>
</template>
