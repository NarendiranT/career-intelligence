<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title: string
  description: string
  icon: Component
  tone: 'blue' | 'purple' | 'green' | 'orange'
}>()

const tones = {
  blue: 'bg-blue-100 text-blue-600',
  purple: 'bg-violet-100 text-violet-600',
  green: 'bg-emerald-100 text-emerald-600',
  orange: 'bg-orange-100 text-orange-500',
}
</script>

<template>
  <li class="flex items-start gap-3">
    <span
      class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
      :class="tones[tone]"
    >
      <component :is="icon" class="h-4 w-4" :stroke-width="2.2" />
    </span>
    <div>
      <p class="text-sm font-semibold text-slate-800">{{ title }}</p>
      <p class="mt-0.5 text-[13px] leading-snug text-slate-500">{{ description }}</p>
    </div>
  </li>
</template>
