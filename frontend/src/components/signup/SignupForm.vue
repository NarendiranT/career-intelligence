<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff, Lock, Mail, User } from '@lucide/vue'
import { ApiError } from '@/api/client'
import { safeNextPath, useAuth } from '@/composables/useAuth'
import { useSocialAuth } from '@/composables/useSocialAuth'
import type { OAuthProvider } from '@/types/auth'
import FormInput from './FormInput.vue'
import SocialButton from './SocialButton.vue'

const route = useRoute()
const router = useRouter()
const { register, loginWithOAuth } = useAuth()
const { googleEnabled, microsoftEnabled, requestIdToken } = useSocialAuth()

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreed = ref(false)
const showPassword = ref(false)
const showConfirm = ref(false)
const submitted = ref(false)
const termsAttempted = ref(false)
const pending = ref(false)
const serverError = ref('')

const termsError = computed(() =>
  (submitted.value || termsAttempted.value) && !agreed.value ? 'Please accept the terms to continue.' : '',
)

const passwordHint = 'Minimum 8 characters with letters, numbers and a symbol'

const passwordOk = computed(() => {
  return /^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/.test(password.value)
})

const passwordsMatch = computed(() => password.value.length > 0 && password.value === confirmPassword.value)

async function onSubmit() {
  submitted.value = true
  serverError.value = ''
  if (!fullName.value.trim() || !email.value.trim() || !passwordOk.value || !passwordsMatch.value || !agreed.value) {
    return
  }
  pending.value = true
  try {
    await register(fullName.value, email.value, password.value)
    await router.replace(safeNextPath(route.query.next))
  } catch (error) {
    serverError.value = error instanceof ApiError ? error.message : 'Could not create your account.'
  } finally {
    pending.value = false
  }
}

async function onSocial(provider: OAuthProvider) {
  serverError.value = ''
  termsAttempted.value = true
  if (!agreed.value) {
    return
  }
  pending.value = true
  try {
    const idToken = await requestIdToken(provider)
    await loginWithOAuth(provider, idToken, true)
    await router.replace(safeNextPath(route.query.next))
  } catch (error) {
    if (error instanceof Error && /cancelled/i.test(error.message)) {
      return
    }
    serverError.value = error instanceof ApiError ? error.message : 'Could not continue with social sign-up.'
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <section class="relative flex min-h-screen flex-col bg-[#f7f8fb] px-5 py-6 sm:px-10">
    <p class="self-end text-sm text-slate-500">
      Already have an account?
      <RouterLink class="font-semibold text-brand hover:text-brand-dark" to="/signin">Sign in</RouterLink>
    </p>

    <div class="flex flex-1 items-center justify-center py-8">
      <div class="w-full max-w-[440px] rounded-2xl bg-white p-8 shadow-[0_20px_50px_rgba(15,23,42,0.08)]">
        <h2 class="text-[1.65rem] font-bold tracking-tight text-slate-900">Create Your Account</h2>
        <p class="mt-2 text-sm leading-relaxed text-slate-500">
          Join Career Intelligence and take the next step in your career journey.
        </p>

        <label class="mt-6 flex items-start gap-2.5 text-[13px] text-slate-600">
          <input
            v-model="agreed"
            class="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
            type="checkbox"
          />
          <span>
            I agree to the
            <RouterLink
              class="font-medium text-brand hover:underline"
              to="/terms"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms of Service
            </RouterLink>
            and
            <RouterLink
              class="font-medium text-brand hover:underline"
              to="/privacy"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </RouterLink>
          </span>
        </label>
        <p v-if="termsError" class="mt-1 text-xs text-red-500">{{ termsError }}</p>

        <div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <SocialButton
            provider="google"
            label="Sign up with Google"
            :disabled="!googleEnabled || pending"
            @click="onSocial('google')"
          />
          <SocialButton
            provider="microsoft"
            label="Sign up with Microsoft"
            :disabled="!microsoftEnabled || pending"
            @click="onSocial('microsoft')"
          />
        </div>

        <div class="my-6 flex items-center gap-3">
          <span class="h-px flex-1 bg-slate-200" />
          <span class="text-xs font-medium tracking-wide text-slate-400">OR</span>
          <span class="h-px flex-1 bg-slate-200" />
        </div>

        <form class="space-y-4" @submit.prevent="onSubmit">
          <FormInput
            v-model="fullName"
            label="Full Name"
            placeholder="John Doe"
            autocomplete="name"
            :error="submitted && !fullName.trim() ? 'Enter your full name.' : ''"
          >
            <template #icon>
              <User class="h-4 w-4" />
            </template>
          </FormInput>

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
            placeholder="Create a strong password"
            autocomplete="new-password"
            :hint="passwordHint"
            :error="submitted && !passwordOk ? 'Use 8+ characters with letters, a number, and a symbol.' : ''"
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

          <FormInput
            v-model="confirmPassword"
            label="Confirm Password"
            :type="showConfirm ? 'text' : 'password'"
            placeholder="Confirm your password"
            autocomplete="new-password"
            :error="submitted && !passwordsMatch ? 'Passwords do not match.' : ''"
          >
            <template #icon>
              <Lock class="h-4 w-4" />
            </template>
            <template #action>
              <button
                class="text-slate-400 hover:text-slate-600"
                type="button"
                :aria-label="showConfirm ? 'Hide password' : 'Show password'"
                @click="showConfirm = !showConfirm"
              >
                <EyeOff v-if="showConfirm" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </template>
          </FormInput>

          <p v-if="serverError" class="text-sm text-red-500">{{ serverError }}</p>

          <button
            class="mt-2 w-full rounded-xl bg-brand py-3 text-[15px] font-semibold text-white shadow-sm transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-70"
            type="submit"
            :disabled="pending"
          >
            {{ pending ? 'Creating account…' : 'Create Account' }}
          </button>
        </form>
      </div>
    </div>

    <p class="pb-2 text-center text-xs text-slate-400">
      Join thousands of professionals making smarter career decisions.
    </p>
  </section>
</template>
