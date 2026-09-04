<script setup lang="ts">
import { Bell, ChevronDown } from '@lucide/vue'
</script>

<template>
  <header class="z-10 flex h-16 shrink-0 items-center justify-end gap-4 border-b border-slate-100 bg-white px-6">
    <button class="relative rounded-full p-2 text-slate-500 hover:bg-slate-50" type="button" aria-label="Notifications">
      <Bell class="h-5 w-5" />
      <span class="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500" />
    </button>
    <button class="flex items-center gap-2 rounded-full py-1 pr-1 pl-1 hover:bg-slate-50" type="button">
      <span class="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-white">
        JD
      </span>
      <span class="text-sm font-medium text-slate-700">John Doe</span>
      <ChevronDown class="h-4 w-4 text-slate-400" />
    </button>
  </header>
</template>
