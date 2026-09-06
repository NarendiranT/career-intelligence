<script setup lang="ts">
import { computed } from 'vue'
import { Copy } from '@lucide/vue'
import InlineMarkdown from '@/components/common/InlineMarkdown.vue'
import { showToast } from '@/composables/useToast'
import { mergeRichBlocks, type RichCode, type RichTable } from '@/utils/richText'

const props = defineProps<{
  text: string
  pending?: boolean
  table?: RichTable
  code?: RichCode
}>()

const blocks = computed(() =>
  mergeRichBlocks(props.text, {
    table: props.table,
    code: props.code,
    pending: props.pending,
  }),
)

async function copyText(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value)
    showToast('Copied to clipboard', 'success')
  } catch {
    showToast('Could not copy', 'error')
  }
}

function headingClass(level: 1 | 2 | 3): string {
  if (level === 1) return 'text-base font-bold text-slate-900'
  if (level === 2) return 'text-sm font-bold text-slate-900'
  return 'text-sm font-semibold text-slate-800'
}
</script>

<template>
  <div class="space-y-3 text-sm leading-relaxed text-slate-800">
    <p v-if="pending && !text.trim()" class="text-slate-500">Thinking…</p>
    <template v-for="(block, index) in blocks" :key="index">
      <h3 v-if="block.type === 'heading'" :class="headingClass(block.level)">
        <InlineMarkdown :text="block.text" />
      </h3>

      <p v-else-if="block.type === 'paragraph'" class="whitespace-pre-wrap">
        <InlineMarkdown :text="block.text" />
        <span v-if="pending && index === blocks.length - 1" class="animate-pulse">▍</span>
      </p>

      <blockquote
        v-else-if="block.type === 'quote'"
        class="rounded-r-lg border-l-2 border-violet-300 bg-violet-50/60 px-3 py-2 text-slate-700"
      >
        <InlineMarkdown :text="block.text" />
      </blockquote>

      <ul v-else-if="block.type === 'list' && !block.ordered" class="list-disc space-y-1 pl-5">
        <li v-for="(item, itemIndex) in block.items" :key="itemIndex">
          <InlineMarkdown :text="item" />
        </li>
      </ul>

      <ol v-else-if="block.type === 'list'" class="list-decimal space-y-1 pl-5">
        <li v-for="(item, itemIndex) in block.items" :key="itemIndex">
          <InlineMarkdown :text="item" />
        </li>
      </ol>

      <div v-else-if="block.type === 'table'" class="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
        <table class="w-full min-w-[360px] border-collapse text-left text-sm">
          <thead class="bg-slate-50 text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
            <tr>
              <th
                v-for="header in block.headers"
                :key="header"
                class="border-b border-slate-200 px-3 py-2.5 whitespace-nowrap"
              >
                <InlineMarkdown :text="header" />
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, rowIndex) in block.rows"
              :key="rowIndex"
              class="border-t border-slate-100 even:bg-slate-50/70"
            >
              <td
                v-for="(cell, cellIndex) in row"
                :key="cellIndex"
                class="px-3 py-2 align-top text-slate-700"
                :class="cellIndex === 0 ? 'font-medium text-slate-800' : ''"
              >
                <InlineMarkdown :text="cell" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else-if="block.type === 'code'" class="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <div class="flex items-center justify-between border-b border-white/10 px-3 py-1.5">
          <span class="text-[11px] font-medium tracking-wide text-slate-400 uppercase">{{ block.language }}</span>
          <button
            class="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-white/10"
            type="button"
            @click="copyText(block.content)"
          >
            <Copy class="h-3 w-3" />
            Copy
          </button>
        </div>
        <pre class="overflow-x-auto p-3 font-mono text-[12px] leading-relaxed text-slate-100"><code>{{ block.content }}</code></pre>
      </div>
    </template>
  </div>
</template>
