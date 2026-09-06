/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_DOWNTIME: string
}

interface GoogleCredentialResponse {
  credential: string
}

interface GoogleAccountsId {
  initialize: (config: {
    client_id: string
    callback: (response: GoogleCredentialResponse) => void
    auto_select?: boolean
    cancel_on_tap_outside?: boolean
  }) => void
  prompt: (momentListener?: (notification: {
    isNotDisplayed: () => boolean
    isSkippedMoment: () => boolean
    isDismissedMoment: () => boolean
  }) => void) => void
}

interface GoogleTokenClient {
  requestAccessToken: (overrideConfig?: { prompt?: string }) => void
}

interface GoogleAccountsOauth2 {
  initTokenClient: (config: {
    client_id: string
    scope: string
    callback: (response: { access_token?: string; error?: string }) => void
    error_callback?: (error: { type?: string; message?: string }) => void
  }) => GoogleTokenClient
}

interface Window {
  google?: {
    accounts: {
      id: GoogleAccountsId
      oauth2: GoogleAccountsOauth2
    }
  }
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
