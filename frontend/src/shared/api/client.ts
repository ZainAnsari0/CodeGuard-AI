/**
 * Shared API client for CodeGuard frontend.
 * Centralizes URL construction, auth, error handling, and response unwrapping.
 *
 * Usage:
 *   import { apiClient } from '../shared/api/client'
 *   const user = await apiClient.get<User>('/api/v1/users/me')
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? ''

export { API_BASE_URL }

/** Custom error class for API errors */
export class ApiError extends Error {
  public readonly status: number
  public readonly code: string
  public readonly details?: Record<string, unknown>

  constructor(status: number, code: string, message: string, details?: Record<string, unknown>) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

// ---------------------------------------------------------------------------
// 401 auto-refresh: transparently refreshes expired access tokens.
// ---------------------------------------------------------------------------

let refreshPromise: Promise<boolean> | null = null

async function tryRefreshToken(): Promise<boolean> {
  // Deduplicate concurrent refresh attempts
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      return res.ok
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | undefined>
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
    const base = this.baseUrl || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost')
    const url = new URL(path.startsWith('http') ? path : `${base}${path}`)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) url.searchParams.set(key, String(value))
      })
    }
    return url.toString()
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let message = `API error: ${response.status}`
      let code = 'UNKNOWN_ERROR'
      let details: Record<string, unknown> | undefined

      try {
        const body = await response.json()
        // New envelope format: { success: false, error: { code, message, details } }
        if (body.error && typeof body.error === 'object') {
          message = body.error.message || message
          code = body.error.code || code
          details = body.error.details
          throw new ApiError(response.status, code, message, details)
        }
        // Legacy format
        message = body.detail || body.message || message
        code = body.code || code
      } catch (e) {
        if (e instanceof ApiError) throw e
        // Response wasn't JSON
      }

      // If still 401 after refresh attempt, redirect to login
      if (response.status === 401) {
        try { sessionStorage.removeItem('auth-storage') } catch { /* ignore */ }
        window.location.href = '/login'
        throw new ApiError(401, 'AUTH_EXPIRED', 'Session expired. Please log in again.')
      }

      throw new ApiError(response.status, code, message)
    }

    const text = await response.text()
    if (!text) return undefined as T

    const json = JSON.parse(text)
    // Unwrap envelope: { success: true, data: T }
    if (json && typeof json === 'object' && 'data' in json) {
      // If data has items (paginated), return data as-is
      if (json.data && typeof json.data === 'object' && 'items' in (json.data as Record<string, unknown>)) {
        return json.data as T
      }
      return json.data as T
    }
    return json as T
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options
    const url = this.buildUrl(path, params)

    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    }

    // Only set Content-Type for JSON bodies (let FormData set its own boundary)
    if (options.body && typeof options.body === 'string') {
      headers['Content-Type'] = 'application/json'
    }

    let response = await fetch(url, { ...fetchOptions, headers, credentials: 'include' })

    // On 401, attempt a token refresh and retry once
    if (response.status === 401) {
      const refreshed = await tryRefreshToken()
      if (refreshed) {
        response = await fetch(url, { ...fetchOptions, headers, credentials: 'include' })
      }
    }

    return this.handleResponse<T>(response)
  }

  async get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
    return this.request<T>(path, { method: 'GET', params })
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, { method: 'POST', body: JSON.stringify(body) })
  }

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type — browser sets it with boundary
    })
  }

  async postUrlEncoded<T>(path: string, data: URLSearchParams): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: data.toString(),
    })
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' })
  }
}

/** Singleton API client instance */
export const apiClient = new ApiClient(API_BASE_URL)