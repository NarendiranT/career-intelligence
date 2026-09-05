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
