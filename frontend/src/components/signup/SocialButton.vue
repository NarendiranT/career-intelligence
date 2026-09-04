<script setup lang="ts">
defineProps<{
  provider: 'google' | 'microsoft'
  label: string
}>()
</script>

<template>
  <button
    class="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-[13px] font-medium text-slate-700 transition hover:bg-slate-50"
    type="button"
  >
    <svg v-if="provider === 'google'" class="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 10.2v3.6h5.1c-.2 1.2-.9 2.2-1.9 2.9l3.1 2.4c1.8-1.7 2.8-4.1 2.8-7 0-.7-.1-1.3-.2-1.9H12z"
      />
      <path
        fill="#34A853"
        d="M6.6 14.3l-.9.7-2.5 1.9C4.8 19.7 8.1 22 12 22c2.7 0 5-.9 6.7-2.4l-3.1-2.4c-.9.6-2 1-3.6 1-2.8 0-5.1-1.9-6-4.4z"
      />
      <path
        fill="#4A90E2"
        d="M3.2 7.1C2.4 8.6 2 10.3 2 12s.4 3.4 1.2 4.9C4.8 19.7 8.1 22 12 22v-3.8c-3.9 0-7.1-2.6-8.2-6.1z"
      />
      <path
        fill="#FBBC05"
        d="M12 4.8c1.7 0 3.2.6 4.4 1.7l3.3-3.3C17 1.1 14.7 0 12 0 8.1 0 4.8 2.3 3.2 7.1l3.4 2.6C7 7.2 9.2 4.8 12 4.8z"
      />
    </svg>
    <svg v-else class="h-4 w-4" viewBox="0 0 23 23" aria-hidden="true">
      <path fill="#F25022" d="M1 1h10v10H1z" />
      <path fill="#00A4EF" d="M12 1h10v10H12z" />
      <path fill="#7FBA00" d="M1 12h10v10H1z" />
      <path fill="#FFB900" d="M12 12h10v10H12z" />
    </svg>
    {{ label }}
  </button>
</template>
