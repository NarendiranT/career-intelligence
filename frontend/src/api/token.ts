const TOKEN_KEY = 'ci.accessToken'
const REMEMBER_EMAIL_KEY = 'ci.rememberEmail'

function localStore(): Storage | null {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

function sessionStore(): Storage | null {
  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

export function readToken(): string | null {
  return localStore()?.getItem(TOKEN_KEY) ?? sessionStore()?.getItem(TOKEN_KEY) ?? null
}

export function writeToken(token: string, persist = true): void {
  const primary = persist ? localStore() : sessionStore()
  const other = persist ? sessionStore() : localStore()
  try {
    primary?.setItem(TOKEN_KEY, token)
    other?.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}

export function clearToken(): void {
  try {
    localStore()?.removeItem(TOKEN_KEY)
    sessionStore()?.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}

export function readRememberedEmail(): string {
  try {
    return localStore()?.getItem(REMEMBER_EMAIL_KEY)?.trim() ?? ''
  } catch {
    return ''
  }
}

export function writeRememberedEmail(email: string | null): void {
  try {
    const store = localStore()
    if (!store) return
    const trimmed = email?.trim() ?? ''
    if (trimmed) store.setItem(REMEMBER_EMAIL_KEY, trimmed)
    else store.removeItem(REMEMBER_EMAIL_KEY)
  } catch {
    /* ignore */
  }
}
