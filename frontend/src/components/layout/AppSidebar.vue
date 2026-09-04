<script setup lang="ts">
import {
  BarChart3,
  Bookmark,
  Briefcase,
  CircleHelp,
  FileText,
  Home,
  MessageSquare,
  Settings,
  Sparkles,
  Upload,
} from '@lucide/vue'

const nav = [
  { label: 'Home', icon: Home, active: false },
  { label: 'Upload Documents', icon: Upload, active: true },
  { label: 'My Documents', icon: FileText, active: false },
  { label: 'Analysis & Insights', icon: BarChart3, active: false },
  { label: 'Chat with Assistant', icon: MessageSquare, active: false },
  { label: 'Saved Results', icon: Bookmark, active: false },
] as const
</script>

<template>
  <aside class="flex h-full w-64 shrink-0 flex-col overflow-hidden border-r border-slate-100 bg-white">
    <div class="flex items-center gap-2.5 px-5 py-5">
      <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-white">
        <Briefcase class="h-5 w-5" :stroke-width="2.2" />
      </span>
      <div>
        <p class="text-[15px] leading-tight font-bold text-slate-800">Career Intelligence</p>
        <p class="text-[11px] text-slate-400">AI-powered career insights</p>
      </div>
    </div>

    <nav class="min-h-0 flex-1 space-y-0.5 overflow-y-auto px-3">
      <div
        v-for="item in nav"
        :key="item.label"
        class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm"
        :class="
          item.active
            ? 'border-l-[3px] border-brand bg-blue-50 font-semibold text-brand'
            : 'font-medium text-slate-500'
        "
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </div>
    </nav>

    <div class="px-4 pb-3">
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

    <div class="space-y-0.5 border-t border-slate-100 px-3 py-3">
      <div class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-500">
        <Settings class="h-4 w-4" />
        Settings
      </div>
      <div class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-500">
        <CircleHelp class="h-4 w-4" />
        Help & Support
      </div>
    </div>
  </aside>
</template>
