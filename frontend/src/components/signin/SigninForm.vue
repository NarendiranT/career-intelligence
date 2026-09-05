<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff, Lock, Mail } from '@lucide/vue'
import { ApiError } from '@/api/client'
import { safeNextPath, useAuth } from '@/composables/useAuth'
import FormInput from '@/components/signup/FormInput.vue'
import SocialButton from '@/components/signup/SocialButton.vue'

const route = useRoute()
const router = useRouter()
const { login } = useAuth()

const email = ref('')
const password = ref('')
const remember = ref(false)
const showPassword = ref(false)
const submitted = ref(false)
const pending = ref(false)
const serverError = ref('')

async function onSubmit() {
  submitted.value = true
  serverError.value = ''
  if (!email.value.trim() || !password.value) {
    return
  }
  pending.value = true
  try {
    await login(email.value, password.value, remember.value)
    await router.replace(safeNextPath(route.query.next))
  } catch (error) {
    serverError.value = error instanceof ApiError ? error.message : 'Could not sign in.'
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <section class="relative flex min-h-screen flex-col bg-[#f7f8fb] px-5 py-6 sm:px-10">
    <p class="self-end text-sm text-slate-500">
      Don’t have an account?
      <RouterLink class="font-semibold text-brand hover:text-brand-dark" to="/">Sign up</RouterLink>
    </p>

    <div class="flex flex-1 items-center justify-center py-8">
      <div class="w-full max-w-[440px] rounded-2xl bg-white p-8 shadow-[0_20px_50px_rgba(15,23,42,0.08)]">
        <h2 class="text-[1.65rem] font-bold tracking-tight text-slate-900">Welcome Back</h2>
        <p class="mt-2 text-sm leading-relaxed text-slate-500">
          Sign in to Career Intelligence and continue your career journey.
        </p>

        <div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <SocialButton provider="google" label="Sign in with Google" disabled />
          <SocialButton provider="microsoft" label="Sign in with Microsoft" disabled />
        </div>

        <div class="my-6 flex items-center gap-3">
          <span class="h-px flex-1 bg-slate-200" />
          <span class="text-xs font-medium tracking-wide text-slate-400">OR</span>
          <span class="h-px flex-1 bg-slate-200" />
        </div>

        <form class="space-y-4" @submit.prevent="onSubmit">
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

          <FormInput
            v-model="password"
            label="Password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Enter your password"
            autocomplete="current-password"
            :error="submitted && !password ? 'Enter your password.' : ''"
          >
            <template #icon>
              <Lock class="h-4 w-4" />
            </template>
            <template #action>
              <button
                class="text-slate-400 hover:text-slate-600"
                type="button"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                @click="showPassword = !showPassword"
              >
                <EyeOff v-if="showPassword" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </template>
          </FormInput>

          <div class="flex items-center justify-between pt-1 text-[13px]">
            <label class="flex items-center gap-2 text-slate-600">
              <input
                v-model="remember"
                class="h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
                type="checkbox"
              />
              Remember me
            </label>
            <a class="font-medium text-brand hover:underline" href="#">Forgot password?</a>
          </div>

          <p v-if="serverError" class="text-sm text-red-500">{{ serverError }}</p>

          <button
            class="mt-2 w-full rounded-xl bg-brand py-3 text-[15px] font-semibold text-white shadow-sm transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-70"
            type="submit"
            :disabled="pending"
          >
            {{ pending ? 'Signing in…' : 'Sign In' }}
          </button>
        </form>
      </div>
    </div>

    <p class="pb-2 text-center text-xs text-slate-400">
      Join thousands of professionals making smarter career decisions.
    </p>
  </section>
</template>
