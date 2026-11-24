import { reactive, readonly } from 'vue'

import { fetchCurrentUser, loginUser, type CurrentUser } from '../api/auth'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '../api/client'

interface AuthState {
  user: CurrentUser | null
  initialized: boolean
}

const state = reactive<AuthState>({
  user: null,
  initialized: false,
})

let restorePromise: Promise<void> | null = null

export const authState = readonly(state)

export function isAuthenticated(): boolean {
  return state.user !== null
}

/**
 * 刷新页面后通过 /api/users/me 恢复用户状态。
 * 无 Token 或 Token 失效时保持未登录，由路由守卫引导到登录页。
 */
export function restoreSession(): Promise<void> {
  if (state.initialized) {
    return Promise.resolve()
  }
  if (restorePromise) {
    return restorePromise
  }

  restorePromise = (async () => {
    if (!getAccessToken()) {
      state.user = null
      state.initialized = true
      return
    }

    try {
      state.user = await fetchCurrentUser()
    } catch {
      // 401 时 API 客户端已清除 Token；网络错误保留 Token，便于刷新后重试。
      state.user = null
    } finally {
      state.initialized = true
      restorePromise = null
    }
  })()

  return restorePromise
}

export async function signIn(
  username: string,
  password: string,
): Promise<void> {
  const { access_token } = await loginUser({ username, password })
  setAccessToken(access_token)

  try {
    state.user = await fetchCurrentUser()
    state.initialized = true
  } catch (error) {
    // 401 时 API 客户端已清除 Token；保留其他错误下的 Token 以便重试。
    state.user = null
    state.initialized = true
    throw error
  }
}

export function signOut(): void {
  clearAccessToken()
  state.user = null
  state.initialized = true
}
