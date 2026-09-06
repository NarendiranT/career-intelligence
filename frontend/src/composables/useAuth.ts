import { computed, ref } from 'vue'
import { fetchMe, loginAccount, logoutAccount, oauthAccount, registerAccount } from '@/api/auth'
import { setUnauthorizedHandler } from '@/api/client'
import { clearToken, readToken, writeToken } from '@/api/token'
import type { AuthUser, OAuthProvider } from '@/types/auth'

const token = ref<string | null>(null)
const user = ref<AuthUser | null>(null)
const bootstrapped = ref(false)

let bootPromise: Promise<void> | null = null
let unauthorizedBound = false

function applySession(accessToken: string, nextUser: AuthUser, persist = true): void {
  writeToken(accessToken, persist)
  token.value = accessToken
  user.value = nextUser
}

function clearSession(): void {
  clearToken()
  token.value = null
  user.value = null
}

export function bootstrapAuth(): Promise<void> {
  if (!unauthorizedBound) {
    unauthorizedBound = true
    setUnauthorizedHandler(() => {
      clearSession()
    })
  }

  if (!bootPromise) {
    bootPromise = (async () => {
      token.value = readToken()
      if (token.value) {
        try {
          user.value = await fetchMe()
        } catch {
          clearSession()
        }
      }
      bootstrapped.value = true
    })().catch(() => {
      clearSession()
      bootstrapped.value = true
    })
  }
  return bootPromise
}

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(token.value && user.value))
  const displayName = computed(() => user.value?.full_name?.trim() || user.value?.email || 'Account')
  const initials = computed(() => {
    const name = user.value?.full_name?.trim()
    if (name) {
      const parts = name.split(/\s+/).filter(Boolean)
      const letters = (parts[0]?.[0] ?? '') + (parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : '')
      return letters.toUpperCase() || 'CI'
    }
    const email = user.value?.email ?? ''
    return (email[0] ?? 'C').toUpperCase()
  })

  async function register(fullName: string, email: string, password: string): Promise<void> {
    const result = await registerAccount({
      full_name: fullName.trim(),
      email: email.trim(),
      password,
    })
    applySession(result.access_token, result.user)
  }

  async function login(email: string, password: string, remember: boolean): Promise<void> {
    const result = await loginAccount({
      email: email.trim(),
      password,
      remember,
    })
    applySession(result.access_token, result.user, remember)
  }

  async function loginWithOAuth(provider: OAuthProvider, idToken: string, remember: boolean): Promise<void> {
    const result = await oauthAccount({
      provider,
      id_token: idToken,
      remember,
    })
    applySession(result.access_token, result.user, remember)
  }

  async function logout(): Promise<void> {
    try {
      await logoutAccount()
    } catch {
      /* client session is cleared regardless */
    }
    clearSession()
  }

  return {
    token,
    user,
    bootstrapped,
    isAuthenticated,
    displayName,
    initials,
    register,
    login,
    loginWithOAuth,
    logout,
  }
}

export function safeNextPath(raw: unknown): string {
  if (typeof raw !== 'string') return '/home'
  if (!raw.startsWith('/') || raw.startsWith('//')) return '/home'
  return raw
}
