export type AuthUser = {
  id: string
  email: string
  full_name: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

export type RegisterPayload = {
  full_name: string
  email: string
  password: string
}

export type LoginPayload = {
  email: string
  password: string
  remember: boolean
}

export type OAuthProvider = 'google' | 'microsoft'

export type OAuthPayload = {
  provider: OAuthProvider
  id_token: string
  remember: boolean
}

export type OAuthConfig = {
  google: boolean
  microsoft: boolean
  google_client_id: string
  microsoft_client_id: string
}
