<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, ChevronDown } from '@lucide/vue'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()
const { token, logout, displayName, initials } = useAuth()
const menuOpen = ref(false)

async function onLogout() {
  menuOpen.value = false
  await logout()
  await router.replace({ name: 'signin' })
}

function onDocumentClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  if (target?.closest('[data-user-menu]')) return
  menuOpen.value = false
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))

watch(token, (value) => {
  if (!value && route.meta.requiresAuth) {
    void router.replace({ name: 'signin', query: { next: route.fullPath } })
  }
})
</script>

<template>
  <header class="z-10 flex h-16 shrink-0 items-center justify-end gap-3 border-b border-slate-100 bg-white px-4 sm:px-6">
    <button class="relative rounded-full p-2 text-slate-500 hover:bg-slate-50" type="button" aria-label="Notifications">
      <Bell class="h-5 w-5" />
      <span class="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500" />
    </button>
    <div class="relative" data-user-menu>
      <button
        class="flex items-center gap-2 rounded-full py-1 pr-1 pl-1 hover:bg-slate-50"
        type="button"
        :aria-expanded="menuOpen"
        aria-haspopup="menu"
        @click="menuOpen = !menuOpen"
      >
        <span class="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-white">
          {{ initials }}
        </span>
        <span class="hidden text-sm font-medium text-slate-700 sm:inline">{{ displayName }}</span>
        <ChevronDown class="h-4 w-4 text-slate-400" />
      </button>
      <div
        v-if="menuOpen"
        class="absolute right-0 z-20 mt-2 w-44 rounded-xl border border-slate-100 bg-white py-1 shadow-lg"
        role="menu"
      >
        <button
          class="block w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
          type="button"
          role="menuitem"
          @click="onLogout"
        >
          Log out
        </button>
      </div>
    </div>
  </header>
</template>
