<script setup lang="ts">
import { ref } from 'vue'
import { Mail } from '@lucide/vue'
import { ApiError } from '@/api/client'
import { requestPasswordReset } from '@/api/auth'
import MarketingPanel from '@/components/signup/MarketingPanel.vue'
import FormInput from '@/components/signup/FormInput.vue'

const email = ref('')
const submitted = ref(false)
const pending = ref(false)
const sent = ref(false)
const serverError = ref('')

async function onSubmit() {
  submitted.value = true
  serverError.value = ''
  if (!email.value.trim()) {
    return
  }
  pending.value = true
  try {
    await requestPasswordReset(email.value)
    sent.value = true
  } catch (error) {
    serverError.value = error instanceof ApiError ? error.message : 'Could not send a reset link.'
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div class="min-h-screen lg:grid lg:grid-cols-2">
    <MarketingPanel />
    <section class="relative flex min-h-screen flex-col bg-[#f7f8fb] px-5 py-6 sm:px-10">
      <p class="self-end text-sm text-slate-500">
        Remembered it?
        <RouterLink class="font-semibold text-brand hover:text-brand-dark" to="/signin">Sign in</RouterLink>
      </p>

      <div class="flex flex-1 items-center justify-center py-8">
        <div class="w-full max-w-[440px] rounded-2xl bg-white p-8 shadow-[0_20px_50px_rgba(15,23,42,0.08)]">
          <template v-if="sent">
            <h2 class="text-[1.65rem] font-bold tracking-tight text-slate-900">Check your email</h2>
            <p class="mt-2 text-sm leading-relaxed text-slate-500">
              If an account exists for {{ email.trim() }}, we sent a link to set a new password.
            </p>
            <RouterLink
              class="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-brand py-3 text-[15px] font-semibold text-white shadow-sm transition hover:bg-brand-dark"
              to="/signin"
            >
              Back to sign in
            </RouterLink>
          </template>
          <template v-else>
            <h2 class="text-[1.65rem] font-bold tracking-tight text-slate-900">Forgot password</h2>
            <p class="mt-2 text-sm leading-relaxed text-slate-500">
              Enter your email and we’ll send a link to reset your password.
            </p>

            <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
              <FormInput
                v-model="email"
                label="Email Address"
                type="email"
                placeholder="you@example.com"
                autocomplete="email"
                :error="submitted && !email.trim() ? 'Enter a valid email address.' : ''"
              >
                <template #icon>
                  <Mail class="h-4 w-4" />
                </template>
              </FormInput>

              <p v-if="serverError" class="text-sm text-red-500">{{ serverError }}</p>

              <button
                class="mt-2 w-full rounded-xl bg-brand py-3 text-[15px] font-semibold text-white shadow-sm transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-70"
                type="submit"
                :disabled="pending"
              >
                {{ pending ? 'Sending…' : 'Send reset link' }}
              </button>
            </form>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>
