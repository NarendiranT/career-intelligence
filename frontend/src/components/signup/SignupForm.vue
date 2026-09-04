<script setup lang="ts">
import { computed, ref } from 'vue'
import { Eye, EyeOff, Lock, Mail, User } from '@lucide/vue'
import FormInput from './FormInput.vue'
import SocialButton from './SocialButton.vue'

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreed = ref(false)
const showPassword = ref(false)
const showConfirm = ref(false)
const submitted = ref(false)

const passwordHint = 'Minimum 8 characters with letters, numbers and a symbol'

const passwordOk = computed(() => {
  return /^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/.test(password.value)
})

const passwordsMatch = computed(() => password.value.length > 0 && password.value === confirmPassword.value)

function onSubmit() {
  submitted.value = true
  if (!fullName.value.trim() || !email.value.trim() || !passwordOk.value || !passwordsMatch.value || !agreed.value) {
    return
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

        <div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <SocialButton provider="google" label="Sign up with Google" />
          <SocialButton provider="microsoft" label="Sign up with Microsoft" />
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

          <label class="flex items-start gap-2.5 pt-1 text-[13px] text-slate-600">
            <input
              v-model="agreed"
              class="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
              type="checkbox"
            />
            <span>
              I agree to the
              <a class="font-medium text-brand hover:underline" href="#">Terms of Service</a>
              and
              <a class="font-medium text-brand hover:underline" href="#">Privacy Policy</a>
            </span>
          </label>
          <p v-if="submitted && !agreed" class="text-xs text-red-500">Please accept the terms to continue.</p>

          <button
            class="mt-2 w-full rounded-xl bg-brand py-3 text-[15px] font-semibold text-white shadow-sm transition hover:bg-brand-dark"
            type="submit"
          >
            Create Account
          </button>
        </form>
      </div>
    </div>

    <p class="pb-2 text-center text-xs text-slate-400">
      Join thousands of professionals making smarter career decisions.
    </p>
  </section>
</template>
