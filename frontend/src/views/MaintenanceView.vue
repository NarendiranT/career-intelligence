<script setup lang="ts">
import { Construction } from '@lucide/vue'
</script>

<template>
  <div class="flex min-h-dvh items-center justify-center bg-[#f5f7fb] p-6">
    <div class="w-full max-w-md rounded-2xl border border-slate-100 bg-white px-8 py-10 text-center shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600">
        <Construction class="h-6 w-6" />
      </span>
      <p class="mt-4 text-[11px] font-bold tracking-[0.16em] text-amber-600 uppercase">Temporarily unavailable</p>
      <h1 class="mt-2 text-xl font-extrabold text-slate-800">Down for Maintenance</h1>
      <p class="mt-3 text-sm leading-relaxed text-slate-500">
        Career Intelligence is offline while we make improvements. Please check back shortly.
      </p>
    </div>
  </div>
</template>
