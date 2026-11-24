import { apiRequest } from './client'

export interface CurrentUser {
  id: number
  username: string
  display_name: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface RegisterPayload {
  username: string
  password: string
  display_name: string
}

export interface LoginPayload {
  username: string
  password: string
}

export function registerUser(payload: RegisterPayload): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/auth/register', {
    method: 'POST',
    body: payload,
  })
}

export function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/api/auth/login', {
    method: 'POST',
    body: payload,
  })
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/users/me')
}
