<script setup lang="ts">
import type { UploadedDoc } from '@/types/upload'
import { fileBadge } from '@/types/upload'
import { FileText, X } from '@lucide/vue'

defineProps<{
  file: UploadedDoc
}>()

defineEmits<{
  remove: []
}>()
</script>

<template>
  <li class="flex items-center gap-3 rounded-xl border border-slate-100 bg-white px-3.5 py-3">
    <span class="flex h-10 w-8 shrink-0 items-center justify-center rounded-md bg-red-50 text-[9px] font-extrabold tracking-wide text-red-500">
      <span class="flex flex-col items-center">
        <FileText class="h-4 w-4" />
        {{ fileBadge(file.name) }}
      </span>
    </span>
    <div class="min-w-0 flex-1">
      <p class="truncate text-sm font-medium text-slate-800">{{ file.name }}</p>
      <p class="mt-0.5 text-xs text-slate-400">{{ file.sizeLabel }} • {{ file.uploadedLabel }}</p>
    </div>
    <button
      class="rounded-md p-1 text-slate-400 hover:bg-slate-50 hover:text-slate-600"
      type="button"
      :aria-label="`Remove ${file.name}`"
      @click="$emit('remove')"
    >
      <X class="h-4 w-4" />
    </button>
  </li>
</template>
