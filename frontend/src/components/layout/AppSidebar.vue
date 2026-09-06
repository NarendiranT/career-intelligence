<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BarChart3,
  Bookmark,
  Briefcase,
  CircleHelp,
  FileText,
  Home,
  MessageSquare,
  Mic,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Settings,
  Sparkles,
  Trash2,
  Upload,
} from '@lucide/vue'
import { useInterview } from '@/composables/useInterview'
import type { ConversationSummary } from '@/types/chat'
import { formatQuestionCount, questionCountLabel } from '@/types/interview'
import { formatRelativeTime } from '@/utils/time'

const route = useRoute()
const router = useRouter()
const { filteredTopics, selectedTopicId, topicQuery, selectTopic } = useInterview()

const props = defineProps<{
  showRecentChats?: boolean
  showInterviewTopics?: boolean
  collapsed?: boolean
  recentChats?: ConversationSummary[]
  activeConversationId?: string | null
}>()

const emit = defineEmits<{
  toggle: []
  selectConversation: [id: string]
  newChat: []
  bookmarkConversation: [id: string, bookmarked: boolean]
  deleteConversation: [id: string]
}>()

const savedChats = computed(() => (props.recentChats ?? []).filter((chat) => chat.bookmarked))
const unsavedChats = computed(() => (props.recentChats ?? []).filter((chat) => !chat.bookmarked))

const nav = [
  { label: 'Home', icon: Home, to: '/home', badge: null },
  { label: 'Upload Documents', icon: Upload, to: '/upload', badge: null },
  { label: 'My Documents', icon: FileText, to: '/documents', badge: null },
  { label: 'Skills', icon: Sparkles, to: '/skills', badge: null },
  { label: 'Usage', icon: BarChart3, to: '/usage', badge: null },
  { label: 'Chat with Assistant', icon: MessageSquare, to: '/chat', badge: null },
  { label: 'Prepare for Interviews', icon: Mic, to: '/interview', badge: null },
] as const

function isActive(to: string | null) {
  return Boolean(to && route.path === to)
}

function chooseInterviewTopic(id: string) {
  selectTopic(id)
  void router.replace({ path: '/interview', query: { topic: id } })
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

    <div v-if="showInterviewTopics && !collapsed" class="mt-4 flex min-h-0 flex-1 flex-col px-3">
      <p class="px-1 text-[11px] font-semibold tracking-wide text-slate-400 uppercase">Interview Topics</p>
      <label class="relative mt-2">
        <Search class="pointer-events-none absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
        <input
          v-model="topicQuery"
          class="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pr-2 pl-8 text-[12px] outline-none placeholder:text-slate-400 focus:border-brand focus:bg-white"
          type="search"
          placeholder="Search topics..."
        />
      </label>
      <div class="mt-2 min-h-0 flex-1 space-y-0.5 overflow-y-auto">
        <button
          v-for="topic in filteredTopics"
          :key="topic.id"
          class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px]"
          :class="
            topic.id === selectedTopicId
              ? 'bg-blue-50 font-semibold text-brand'
              : 'font-medium text-slate-600 hover:bg-slate-50'
          "
          type="button"
          :title="questionCountLabel(topic.question_count)"
          @click="chooseInterviewTopic(topic.id)"
        >
          <span class="min-w-0 flex-1 truncate">{{ topic.label }}</span>
          <span
            class="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums"
            :class="
              topic.id === selectedTopicId ? 'bg-blue-100 text-brand' : 'bg-slate-100 text-slate-500'
            "
            :aria-label="questionCountLabel(topic.question_count)"
          >
            {{ formatQuestionCount(topic.question_count) }}
          </span>
        </button>
        <p v-if="!filteredTopics.length" class="px-2 py-3 text-[12px] text-slate-400">
          {{ topicQuery.trim() ? 'No topics match.' : 'No topics yet. Create them from a chat reply.' }}
        </p>
      </div>
    </div>

    <div v-else-if="showRecentChats && !collapsed" class="mt-5 min-h-0 flex-1 overflow-y-auto px-3">
      <section v-if="savedChats.length" class="mb-4">
        <p class="mb-1 px-1 text-[11px] font-semibold tracking-wide text-orange-500 uppercase">Saved Results</p>
        <button
          v-for="chat in savedChats"
          :key="chat.id"
          class="group mb-1 flex w-full items-start gap-1 rounded-lg px-2 py-2 text-left"
          :class="chat.id === props.activeConversationId ? 'bg-orange-50' : 'hover:bg-slate-50'"
          type="button"
          @click="emit('selectConversation', chat.id)"
        >
          <span class="min-w-0 flex-1">
            <p
              class="truncate text-[13px] font-medium"
              :class="chat.id === props.activeConversationId ? 'text-orange-600' : 'text-slate-700'"
            >
              {{ chat.title }}
            </p>
            <p class="mt-0.5 text-[11px] text-slate-400">{{ formatRelativeTime(chat.updated_at) }}</p>
          </span>
          <span class="flex shrink-0 items-center gap-0.5 opacity-80 group-hover:opacity-100">
            <span
              class="rounded p-1 text-orange-500 hover:bg-white"
              role="button"
              tabindex="0"
              aria-label="Remove bookmark"
              @click.stop="emit('bookmarkConversation', chat.id, false)"
              @keydown.enter.stop="emit('bookmarkConversation', chat.id, false)"
            >
              <Bookmark class="h-3.5 w-3.5 fill-current" />
            </span>
            <span
              class="rounded p-1 text-slate-400 hover:bg-white hover:text-red-500"
              role="button"
              tabindex="0"
              aria-label="Delete chat"
              @click.stop="emit('deleteConversation', chat.id)"
              @keydown.enter.stop="emit('deleteConversation', chat.id)"
            >
              <Trash2 class="h-3.5 w-3.5" />
            </span>
          </span>
        </button>
      </section>
      <div class="mb-2 flex items-center justify-between px-1">
        <p class="text-[11px] font-semibold tracking-wide text-slate-400 uppercase">Recent Chats</p>
        <button
          class="inline-flex items-center gap-1 text-[11px] font-semibold text-brand"
          type="button"
          @click="emit('newChat')"
        >
          <Plus class="h-3 w-3" />
          New Chat
        </button>
      </div>
      <p v-if="!unsavedChats.length && !savedChats.length" class="px-2 py-3 text-[12px] text-slate-400">
        No conversations yet.
      </p>
      <p v-else-if="!unsavedChats.length" class="px-2 py-2 text-[12px] text-slate-400">No other recent chats.</p>
      <button
        v-for="chat in unsavedChats"
        :key="chat.id"
        class="group mb-1 flex w-full items-start gap-1 rounded-lg px-2 py-2 text-left"
        :class="chat.id === props.activeConversationId ? 'bg-blue-50' : 'hover:bg-slate-50'"
        type="button"
        @click="emit('selectConversation', chat.id)"
      >
        <span class="min-w-0 flex-1">
          <p
            class="truncate text-[13px] font-medium"
            :class="chat.id === props.activeConversationId ? 'text-brand' : 'text-slate-700'"
          >
            {{ chat.title }}
          </p>
          <p class="mt-0.5 text-[11px] text-slate-400">{{ formatRelativeTime(chat.updated_at) }}</p>
        </span>
        <span class="flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100">
          <span
            class="rounded p-1 text-slate-400 hover:bg-white hover:text-orange-500"
            role="button"
            tabindex="0"
            aria-label="Bookmark chat"
            @click.stop="emit('bookmarkConversation', chat.id, true)"
            @keydown.enter.stop="emit('bookmarkConversation', chat.id, true)"
          >
            <Bookmark class="h-3.5 w-3.5" />
          </span>
          <span
            class="rounded p-1 text-slate-400 hover:bg-white hover:text-red-500"
            role="button"
            tabindex="0"
            aria-label="Delete chat"
            @click.stop="emit('deleteConversation', chat.id)"
            @keydown.enter.stop="emit('deleteConversation', chat.id)"
          >
            <Trash2 class="h-3.5 w-3.5" />
          </span>
        </span>
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
