<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff, Lock } from '@lucide/vue'
import { ApiError } from '@/api/client'
import { resetPassword } from '@/api/auth'
import MarketingPanel from '@/components/signup/MarketingPanel.vue'
import FormInput from '@/components/signup/FormInput.vue'

const route = useRoute()
const router = useRouter()
const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : ''))

const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirm = ref(false)
const submitted = ref(false)
const pending = ref(false)
const serverError = ref('')

const passwordOk = computed(() => /^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/.test(password.value))
const passwordsMatch = computed(() => password.value.length > 0 && password.value === confirmPassword.value)

async function onSubmit() {
  submitted.value = true
  serverError.value = ''
  if (!token.value || !passwordOk.value || !passwordsMatch.value) {
    return
  }
  pending.value = true
  try {
    await resetPassword(token.value, password.value)
    await router.replace({ name: 'signin' })
  } catch (error) {
    serverError.value = error instanceof ApiError ? error.message : 'Could not reset your password.'
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
        <RouterLink class="font-semibold text-brand hover:text-brand-dark" to="/signin">Sign in</RouterLink>
      </p>

      <div class="flex flex-1 items-center justify-center py-8">
        <div class="w-full max-w-[440px] rounded-2xl bg-white p-8 shadow-[0_20px_50px_rgba(15,23,42,0.08)]">
          <template v-if="!token">
            <h2 class="text-[1.65rem] font-bold tracking-tight text-slate-900">Link expired</h2>
            <p class="mt-2 text-sm leading-relaxed text-slate-500">
              This reset link is missing or invalid. Request a new one from the forgot password page.
            </p>
            <RouterLink
              class="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-brand py-3 text-[15px] font-semibold text-white shadow-sm transition hover:bg-brand-dark"
              to="/forgot-password"
            >
              Forgot password
            </RouterLink>
          </template>
          <template v-else>
            <h2 class="text-[1.65rem] font-bold tracking-tight text-slate-900">Set a new password</h2>
            <p class="mt-2 text-sm leading-relaxed text-slate-500">
              Choose a password with at least 8 characters, including letters, a number, and a symbol.
            </p>

            <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
              <FormInput
                v-model="password"
                label="New password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter a new password"
                autocomplete="new-password"
                :error="submitted && !passwordOk ? 'Password must be at least 8 characters with letters, a number, and a symbol.' : ''"
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
                label="Confirm password"
                :type="showConfirm ? 'text' : 'password'"
                placeholder="Re-enter your password"
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
                {{ pending ? 'Saving…' : 'Update password' }}
              </button>
            </form>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>
