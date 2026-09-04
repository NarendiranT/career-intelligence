<script setup lang="ts">
import { ref } from 'vue'
import { CloudUpload, FolderOpen } from '@lucide/vue'
import { ACCEPTED_TYPES, isAcceptedFile } from '@/types/upload'

const props = defineProps<{
  multiple?: boolean
  buttonLabel: string
  title: string
  hint: string
}>()

const emit = defineEmits<{
  files: [files: File[]]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const dragging = ref(false)

function openPicker() {
  inputRef.value?.click()
}

function takeFiles(list: FileList | File[] | null) {
  if (!list) return
  const files = Array.from(list).filter(isAcceptedFile)
  if (files.length) emit('files', files)
}

function onDrop(event: DragEvent) {
  dragging.value = false
  takeFiles(event.dataTransfer?.files ?? null)
}
</script>

<template>
  <div
    class="rounded-2xl border-2 border-dashed px-6 py-10 text-center transition"
    :class="dragging ? 'border-brand bg-blue-50' : 'border-sky-200 bg-[#f7fbff]'"
    @dragenter.prevent="dragging = true"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <input
      ref="inputRef"
      class="hidden"
      type="file"
      :accept="ACCEPTED_TYPES"
      :multiple="props.multiple"
      @change="takeFiles(($event.target as HTMLInputElement).files); ($event.target as HTMLInputElement).value = ''"
    />
    <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white text-sky-500 shadow-sm">
      <CloudUpload class="h-6 w-6" />
    </span>
    <p class="mt-4 text-sm font-medium text-slate-700">{{ title }}</p>
    <p class="mt-1 text-xs text-slate-400">{{ hint }}</p>
    <button
      class="mt-5 inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-dark"
      type="button"
      @click="openPicker"
    >
      <FolderOpen class="h-4 w-4" />
      {{ buttonLabel }}
    </button>
  </div>
</template>
