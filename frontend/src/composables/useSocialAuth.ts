import { onMounted, ref } from 'vue'
import { PublicClientApplication } from '@azure/msal-browser'
import { fetchOAuthConfig } from '@/api/auth'
import type { OAuthProvider } from '@/types/auth'

const GIS_SRC = 'https://accounts.google.com/gsi/client'

let msalApp: PublicClientApplication | null = null
let googleScriptPromise: Promise<void> | null = null
const googleClientId = ref('')
const microsoftClientId = ref('')

function loadGoogleScript(): Promise<void> {
  if (window.google?.accounts?.oauth2) {
    return Promise.resolve()
  }
  if (!googleScriptPromise) {
    googleScriptPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SRC}"]`)
      if (existing) {
        existing.addEventListener('load', () => resolve())
        existing.addEventListener('error', () => reject(new Error('Could not load Google Sign-In.')))
        return
      }
      const script = document.createElement('script')
      script.src = GIS_SRC
      script.async = true
      script.onload = () => resolve()
      script.onerror = () => reject(new Error('Could not load Google Sign-In.'))
      document.head.appendChild(script)
    })
  }
  return googleScriptPromise
}

async function getMsal(clientId: string): Promise<PublicClientApplication> {
  if (!msalApp) {
    msalApp = new PublicClientApplication({
      auth: {
        clientId,
        authority: 'https://login.microsoftonline.com/common',
        redirectUri: window.location.origin,
      },
      cache: {
        cacheLocation: 'sessionStorage',
      },
    })
    await msalApp.initialize()
  }
  return msalApp
}

export function useSocialAuth() {
  const googleEnabled = ref(false)
  const microsoftEnabled = ref(false)

  onMounted(async () => {
    try {
      const config = await fetchOAuthConfig()
      googleClientId.value = config.google_client_id.trim()
      microsoftClientId.value = config.microsoft_client_id.trim()
      googleEnabled.value = Boolean(config.google && googleClientId.value)
      microsoftEnabled.value = Boolean(config.microsoft && microsoftClientId.value)
    } catch {
      googleEnabled.value = false
      microsoftEnabled.value = false
    }
  })

  async function requestGoogleIdToken(): Promise<string> {
    const clientId = googleClientId.value
    if (!clientId) {
      throw new Error('Google Sign-In is not configured.')
    }
    await loadGoogleScript()
    const oauth2 = window.google?.accounts?.oauth2
    if (!oauth2) {
      throw new Error('Google Sign-In is unavailable.')
    }
    return new Promise((resolve, reject) => {
      const client = oauth2.initTokenClient({
        client_id: clientId,
        scope: 'openid email profile',
        callback: (response) => {
          if (response.access_token) {
            resolve(response.access_token)
            return
          }
          if (response.error === 'popup_closed_by_user' || response.error === 'access_denied') {
            reject(new Error('Google sign-in was cancelled.'))
            return
          }
          reject(new Error('Google did not return an identity token.'))
        },
        error_callback: (error) => {
          const type = error.type ?? ''
          if (type === 'popup_closed' || type === 'popup_failed_to_open') {
            reject(new Error('Google sign-in was cancelled.'))
            return
          }
          reject(new Error(error.message || 'Google Sign-In is unavailable.'))
        },
      })
      client.requestAccessToken({ prompt: 'select_account' })
    })
  }

  async function requestMicrosoftIdToken(): Promise<string> {
    const clientId = microsoftClientId.value
    if (!clientId) {
      throw new Error('Microsoft Sign-In is not configured.')
    }
    const app = await getMsal(clientId)
    try {
      const result = await app.loginPopup({
        scopes: ['openid', 'profile', 'email'],
      })
      if (!result.idToken) {
        throw new Error('Microsoft did not return an identity token.')
      }
      return result.idToken
    } catch (error) {
      const code =
        error && typeof error === 'object' && 'errorCode' in error
          ? String((error as { errorCode: unknown }).errorCode)
          : ''
      if (code.includes('user_cancelled') || code.includes('popup_closed')) {
        throw new Error('Microsoft sign-in was cancelled.')
      }
      throw error
    }
  }

  async function requestIdToken(provider: OAuthProvider): Promise<string> {
    if (provider === 'google') {
      return requestGoogleIdToken()
    }
    return requestMicrosoftIdToken()
  }

  return {
    googleEnabled,
    microsoftEnabled,
    requestIdToken,
  }
}
