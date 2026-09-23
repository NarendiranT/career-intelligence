import { apiFetch } from './client'
import type { AuthUser, LoginPayload, OAuthConfig, OAuthPayload, RegisterPayload, TokenResponse } from '@/types/auth'

export function registerAccount(payload: RegisterPayload): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/v1/auth/register', {
    method: 'POST',
    json: payload,
    skipAuth: true,
  })
}

export function loginAccount(payload: LoginPayload): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/v1/auth/login', {
    method: 'POST',
    json: payload,
    skipAuth: true,
  })
}

export function requestPasswordReset(email: string): Promise<void> {
  return apiFetch<void>('/v1/auth/forgot-password', {
    method: 'POST',
    json: { email: email.trim() },
    skipAuth: true,
  })
}

export function resetPassword(token: string, password: string): Promise<void> {
  return apiFetch<void>('/v1/auth/reset-password', {
    method: 'POST',
    json: { token, password },
    skipAuth: true,
  })
}

export function fetchMe(): Promise<AuthUser> {
  return apiFetch<AuthUser>('/v1/auth/me')
}

export function logoutAccount(): Promise<void> {
  return apiFetch<void>('/v1/auth/logout', { method: 'POST', skipAuth: true })
}

export function fetchOAuthConfig(): Promise<OAuthConfig> {
  return apiFetch<OAuthConfig>('/v1/auth/oauth/config', { skipAuth: true })
}

export function oauthAccount(payload: OAuthPayload): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/v1/auth/oauth', {
    method: 'POST',
    json: payload,
    skipAuth: true,
  })
}
