const TOKEN_KEY = 'medalsoft.access_token'

export interface ApiErrorPayload {
  code?: string
  message?: string
  details?: Record<string, unknown>
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown> | undefined

  constructor(
    status: number,
    code: string,
    message: string,
    details?: Record<string, unknown>,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}

let unauthorizedHandler: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const token = getAccessToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let response: Response
  try {
    response = await fetch(path, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, 'network_error', '网络连接失败，请检查网络后重试')
  }

  const isJson = (response.headers.get('content-type') ?? '').includes(
    'application/json',
  )
  let data: unknown = null
  if (isJson) {
    try {
      data = await response.json()
    } catch {
      data = null
    }
  }

  if (!response.ok) {
    const payload = (data ?? {}) as ApiErrorPayload
    const error = new ApiError(
      response.status,
      payload.code ?? `http_${response.status}`,
      payload.message ?? '请求失败，请稍后重试',
      payload.details,
    )

    if (response.status === 401) {
      clearAccessToken()
      unauthorizedHandler?.()
    }

    throw error
  }

  return data as T
}

/** 从后端 details 中取出某个字段的可展示错误。 */
export function fieldMessages(
  details: Record<string, unknown> | undefined,
  field: string,
): string[] {
  if (!details) return []
  const value = details[field]
  if (typeof value === 'string') return [value]
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === 'string')
  }
  return []
}
