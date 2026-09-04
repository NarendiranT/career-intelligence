<script setup lang="ts">
defineProps<{
  label: string
  modelValue: string
  placeholder?: string
  type?: string
  autocomplete?: string
  hint?: string
  error?: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <label class="block">
    <span class="mb-1.5 block text-[13px] font-medium text-slate-700">{{ label }}</span>
    <span
      class="flex items-center gap-2 rounded-xl border bg-white px-3 py-2.5 transition"
      :class="error ? 'border-red-300 focus-within:border-red-400' : 'border-slate-200 focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/15'"
    >
      <span class="text-slate-400">
        <slot name="icon" />
      </span>
      <input
        class="w-full bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400"
        :value="modelValue"
        :type="type ?? 'text'"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
      <slot name="action" />
    </span>
    <span v-if="error" class="mt-1 block text-xs text-red-500">{{ error }}</span>
    <span v-else-if="hint" class="mt-1 block text-xs text-slate-400">{{ hint }}</span>
  </label>
</template>
