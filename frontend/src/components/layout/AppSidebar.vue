<script setup lang="ts">
import { useRoute } from 'vue-router'
import {
  BarChart3,
  Bookmark,
  Briefcase,
  CircleHelp,
  FileText,
  Home,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Settings,
  Sparkles,
  Upload,
} from '@lucide/vue'

const route = useRoute()

defineProps<{
  showRecentChats?: boolean
  collapsed?: boolean
}>()

defineEmits<{
  toggle: []
}>()

const nav = [
  { label: 'Home', icon: Home, to: '/home', badge: null },
  { label: 'Upload Documents', icon: Upload, to: '/upload', badge: null },
  { label: 'My Documents', icon: FileText, to: '/documents', badge: null },
  { label: 'Analysis & Insights', icon: BarChart3, to: '/analysis', badge: 'Soon' },
  { label: 'Chat with Assistant', icon: MessageSquare, to: '/chat', badge: null },
  { label: 'Saved Results', icon: Bookmark, to: null, badge: null },
] as const

const recentChats = [
  { title: 'Job Fit for Senior AI Engineer', time: '2 minutes ago', active: true },
  { title: 'Compare two roles', time: '1 hour ago', active: false },
  { title: 'Skill gap analysis', time: 'Yesterday', active: false },
  { title: 'Interview preparation', time: '2 days ago', active: false },
  { title: 'AWS experience details', time: '3 days ago', active: false },
]

function isActive(to: string | null) {
  return Boolean(to && route.path === to)
}
</script>

<template>
  <aside
    class="flex h-full shrink-0 flex-col overflow-hidden border-r border-slate-100 bg-white transition-[width] duration-200"
    :class="collapsed ? 'w-16' : 'w-64'"
  >
    <div class="flex items-center gap-2 py-4" :class="collapsed ? 'justify-center px-2' : 'px-4'">
      <button
        v-if="collapsed"
        class="group relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand text-white"
        type="button"
        title="Expand sidebar"
        aria-label="Expand left sidebar"
        @click="$emit('toggle')"
      >
        <Briefcase class="h-5 w-5 transition-opacity duration-150 group-hover:opacity-0" :stroke-width="2.2" />
        <PanelLeftOpen
          class="absolute h-5 w-5 opacity-0 transition-opacity duration-150 group-hover:opacity-100"
          :stroke-width="2.2"
        />
      </button>
      <span
        v-else
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand text-white"
      >
        <Briefcase class="h-5 w-5" :stroke-width="2.2" />
      </span>
      <div v-if="!collapsed" class="min-w-0 flex-1">
        <p class="truncate text-[15px] leading-tight font-bold text-slate-800">Career Intelligence</p>
        <p class="truncate text-[11px] text-slate-400">AI-powered career insights</p>
      </div>
      <button
        v-if="!collapsed"
        class="rounded-lg p-1.5 text-slate-400 hover:bg-slate-50 hover:text-slate-700"
        type="button"
        aria-label="Minimize left sidebar"
        @click="$emit('toggle')"
      >
        <PanelLeftClose class="h-4 w-4" />
      </button>
    </div>

    <nav class="space-y-0.5 px-2">
      <component
        :is="item.to ? 'RouterLink' : 'div'"
        v-for="item in nav"
        :key="item.label"
        :to="item.to ?? undefined"
        class="flex items-center rounded-lg py-2.5 text-sm"
        :class="[
          collapsed ? 'justify-center px-0' : 'gap-3 px-3',
          isActive(item.to)
            ? 'border-l-[3px] border-brand bg-blue-50 font-semibold text-brand'
            : 'font-medium text-slate-500',
        ]"
        :title="collapsed ? (item.badge ? `${item.label} (${item.badge})` : item.label) : undefined"
      >
        <component :is="item.icon" class="h-4 w-4 shrink-0" />
        <span v-if="!collapsed" class="min-w-0 flex-1 truncate">{{ item.label }}</span>
        <span
          v-if="!collapsed && item.badge"
          class="rounded-full bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600"
        >
          {{ item.badge }}
        </span>
      </component>
    </nav>

    <div v-if="showRecentChats && !collapsed" class="mt-5 min-h-0 flex-1 overflow-y-auto px-3">
      <div class="mb-2 flex items-center justify-between px-1">
        <p class="text-[11px] font-semibold tracking-wide text-slate-400 uppercase">Recent Chats</p>
        <button class="inline-flex items-center gap-1 text-[11px] font-semibold text-brand" type="button">
          <Plus class="h-3 w-3" />
          New Chat
        </button>
      </div>
      <button
        v-for="chat in recentChats"
        :key="chat.title"
        class="mb-1 w-full rounded-lg px-3 py-2 text-left"
        :class="chat.active ? 'bg-blue-50' : 'hover:bg-slate-50'"
        type="button"
      >
        <p class="truncate text-[13px] font-medium" :class="chat.active ? 'text-brand' : 'text-slate-700'">
          {{ chat.title }}
        </p>
        <p class="mt-0.5 text-[11px] text-slate-400">{{ chat.time }}</p>
      </button>
    </div>

    <div v-else-if="!collapsed" class="min-h-0 flex-1 overflow-y-auto px-4 pt-4">
      <div class="rounded-2xl bg-[#eef5ff] p-4">
        <div class="flex items-start justify-between gap-2">
          <p class="text-[13px] font-semibold text-slate-800">Turn your experience into opportunity</p>
          <Sparkles class="h-5 w-5 shrink-0 text-violet-500" />
        </div>
        <p class="mt-2 text-[12px] leading-relaxed text-slate-500">
          Get personalized insights, find skill gaps, and prepare for your next role.
        </p>
      </div>
    </div>

    <div v-else class="min-h-0 flex-1" />

    <div class="space-y-0.5 border-t border-slate-100 px-2 py-3">
      <div
        class="flex items-center rounded-lg py-2.5 text-sm font-medium text-slate-500"
        :class="collapsed ? 'justify-center' : 'gap-3 px-3'"
        title="Settings"
      >
        <Settings class="h-4 w-4 shrink-0" />
        <span v-if="!collapsed">Settings</span>
      </div>
      <div
        class="flex items-center rounded-lg py-2.5 text-sm font-medium text-slate-500"
        :class="collapsed ? 'justify-center' : 'gap-3 px-3'"
        title="Help & Support"
      >
        <CircleHelp class="h-4 w-4 shrink-0" />
        <span v-if="!collapsed">Help & Support</span>
      </div>
    </div>
  </aside>
</template>
