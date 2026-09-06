<script setup lang="ts">
import { parseInline } from '@/utils/richText'

defineProps<{
  text: string
}>()
</script>

<template>
  <template v-for="(part, partIndex) in parseInline(text)" :key="partIndex">
    <code
      v-if="part.type === 'code'"
      class="rounded bg-slate-100 px-1 py-0.5 font-mono text-[12px] text-violet-700"
    >{{ part.value }}</code>
    <strong v-else-if="part.type === 'bold'">{{ part.value }}</strong>
    <em v-else-if="part.type === 'italic'">{{ part.value }}</em>
    <template v-else>{{ part.value }}</template>
  </template>
</template>
