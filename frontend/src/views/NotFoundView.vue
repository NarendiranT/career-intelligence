<script setup lang="ts">
import { FileQuestion } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated } = useAuth()
</script>

<template>
  <div class="flex min-h-dvh items-center justify-center bg-[#f5f7fb] p-6">
    <div class="w-full max-w-md rounded-2xl border border-slate-100 bg-white px-8 py-10 text-center shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-brand">
        <FileQuestion class="h-6 w-6" />
      </span>
      <p class="mt-4 text-[11px] font-bold tracking-[0.16em] text-brand uppercase">Error 404</p>
      <h1 class="mt-2 text-xl font-extrabold text-slate-800">Page not found</h1>
      <p class="mt-3 text-sm leading-relaxed text-slate-500">
        That URL doesn’t exist. Check the address or go back to a page that does.
      </p>
      <RouterLink
        :to="isAuthenticated ? '/home' : '/'"
        class="mt-6 inline-flex items-center justify-center rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark"
      >
        {{ isAuthenticated ? 'Back to Home' : 'Go to Career Intelligence' }}
      </RouterLink>
    </div>
  </div>
</template>
