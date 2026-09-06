<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Download, LoaderCircle, X } from '@lucide/vue'
import { fetchUsageActivities } from '@/api/usage'
import type { UsageActivity, UsageFeature, UsageFeatureId } from '@/types/usage'

const FEATURE_COLORS: Record<UsageFeatureId, string> = {
  chat: '#2563eb',
  interview: '#8b5cf6',
  documents: '#10b981',
}

const props = defineProps<{
  open: boolean
  start: string
  end: string
  featureMeta: (id: UsageFeatureId) => UsageFeature
  featureIcons: Record<UsageFeatureId, unknown>
  formatDateTime: (value: string) => string
  formatTokens: (value: number) => string
}>()

const emit = defineEmits<{ close: []; 'update:start': [string]; 'update:end': [string] }>()

const loading = ref(false)
const error = ref('')
const rows = ref<UsageActivity[]>([])

const startModel = computed({
  get: () => props.start,
  set: (value: string) => emit('update:start', value),
})

const endModel = computed({
  get: () => props.end,
  set: (value: string) => emit('update:end', value),
})

function csvCell(value: string | number): string {
  const text = String(value)
  if (/[",\n]/.test(text)) return `"${text.replaceAll('"', '""')}"`
  return text
}

function exportUsage(): void {
  const header = ['Date & Time', 'Feature', 'Tokens Used', 'Details']
  const lines = [
    header.join(','),
    ...rows.value.map((row) =>
      [
        csvCell(props.formatDateTime(row.created_at)),
        csvCell(props.featureMeta(row.feature).label),
        csvCell(row.tokens),
        csvCell(row.details),
      ].join(','),
    ),
  ]
  const blob = new Blob([`${lines.join('\n')}\n`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `usage-${props.start}-to-${props.end}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

async function loadActivities(): Promise<void> {
  if (!props.open) return
  loading.value = true
  error.value = ''
  try {
    const data = await fetchUsageActivities(props.start, props.end)
    rows.value = data.activities
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load usage.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) emit('close')
}

watch(
  () => [props.open, props.start, props.end] as const,
  ([open]) => {
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) void loadActivities()
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-slate-900/50 p-4"
      role="presentation"
      @click.self="emit('close')"
    >
      <div
        class="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-[0_24px_64px_rgba(15,23,42,0.28)]"
        role="dialog"
        aria-modal="true"
        aria-label="All usage"
      >
        <header class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3">
          <div>
            <h2 class="text-sm font-semibold text-slate-800">All usage</h2>
            <p class="text-xs text-slate-400">Filter by date and export the matching activity.</p>
          </div>
          <button
            class="rounded-lg p-1.5 text-slate-400 hover:bg-slate-50 hover:text-slate-700"
            type="button"
            aria-label="Close usage"
            @click="emit('close')"
          >
            <X class="h-4 w-4" />
          </button>
        </header>

        <div class="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-3">
          <div class="flex flex-wrap items-end gap-3">
            <label class="text-xs font-medium text-slate-500">
              From
              <input
                v-model="startModel"
                type="date"
                class="mt-1 block rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 outline-none focus:border-brand focus:ring-2 focus:ring-brand/15"
              />
            </label>
            <label class="text-xs font-medium text-slate-500">
              To
              <input
                v-model="endModel"
                type="date"
                class="mt-1 block rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 outline-none focus:border-brand focus:ring-2 focus:ring-brand/15"
              />
            </label>
          </div>
          <button
            class="inline-flex items-center gap-2 rounded-xl bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            :disabled="loading || rows.length === 0"
            @click="exportUsage"
          >
            <Download class="h-4 w-4" />
            Export usage
          </button>
        </div>

        <p v-if="error" class="mx-5 mt-3 rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-600">
          {{ error }}
        </p>

        <div class="min-h-0 flex-1 overflow-auto px-5 py-3">
          <div v-if="loading" class="flex items-center justify-center gap-2 py-16 text-sm text-slate-400">
            <LoaderCircle class="h-4 w-4 animate-spin" />
            Loading
          </div>
          <div v-else-if="rows.length === 0" class="py-16 text-center text-sm text-slate-400">
            No usage in this date range.
          </div>
          <table v-else class="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr class="border-b border-slate-100 text-[11px] font-semibold tracking-wide text-slate-400 uppercase">
                <th class="py-2 pr-3 font-semibold">Date & Time</th>
                <th class="py-2 pr-3 font-semibold">Feature</th>
                <th class="py-2 pr-3 font-semibold">Tokens Used</th>
                <th class="py-2 font-semibold">Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.id" class="border-b border-slate-50 last:border-0">
                <td class="py-3 pr-3 whitespace-nowrap text-slate-500">{{ formatDateTime(row.created_at) }}</td>
                <td class="py-3 pr-3">
                  <span class="inline-flex items-center gap-2 font-medium text-slate-700">
                    <span
                      class="flex h-7 w-7 items-center justify-center rounded-lg"
                      :style="{ backgroundColor: `${FEATURE_COLORS[row.feature]}14`, color: FEATURE_COLORS[row.feature] }"
                    >
                      <component :is="featureIcons[row.feature]" class="h-3.5 w-3.5" />
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
      </div>
    </div>
  </Teleport>
</template>
