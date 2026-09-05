<script setup lang="ts">
import { computed, useSlots } from 'vue'
import { PanelRightClose, PanelRightOpen } from '@lucide/vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopBar from '@/components/layout/AppTopBar.vue'
import { useSidebar } from '@/composables/useSidebar'

defineProps<{
  showRecentChats?: boolean
  showInterviewTopics?: boolean
}>()

const slots = useSlots()
const hasRight = computed(() => Boolean(slots.right))
const { leftCollapsed, rightCollapsed, toggleLeft, toggleRight } = useSidebar()
</script>

<template>
  <div class="flex h-dvh overflow-hidden bg-[#f5f7fb]">
    <AppSidebar
      :collapsed="leftCollapsed"
      :show-recent-chats="showRecentChats"
      :show-interview-topics="showInterviewTopics"
      @toggle="toggleLeft"
    />

    <div class="flex min-h-0 min-w-0 flex-1 flex-col">
      <AppTopBar />

      <div class="flex min-h-0 flex-1">
        <div class="min-h-0 min-w-0 flex-1 overflow-hidden">
          <slot />
        </div>

        <template v-if="hasRight">
          <aside
            v-if="rightCollapsed"
            class="flex h-full w-12 shrink-0 flex-col items-center border-l border-slate-100 bg-white py-3"
          >
            <button
              class="rounded-lg p-2 text-slate-500 hover:bg-slate-50 hover:text-slate-800"
              type="button"
              aria-label="Expand right sidebar"
              @click="toggleRight"
            >
              <PanelRightOpen class="h-4 w-4" />
            </button>
          </aside>
          <div v-else class="flex h-full min-h-0 shrink-0 flex-col border-l border-slate-100 bg-white">
            <div class="flex h-12 shrink-0 items-center justify-end px-2">
              <button
                class="rounded-lg p-2 text-slate-400 hover:bg-slate-50 hover:text-slate-700"
                type="button"
                aria-label="Minimize right sidebar"
                @click="toggleRight"
              >
                <PanelRightClose class="h-4 w-4" />
              </button>
            </div>
            <div class="min-h-0 flex-1 overflow-hidden">
              <slot name="right" />
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
