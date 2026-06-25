/**
 * Shared API utilities for CodeGuard frontend.
 * Eliminates duplicated unwrap/apiFetch/API_BASE_URL across hooks and pages.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export { API_BASE_URL }

/**
 * Unwrap a paginated or data-wrapped API response.
 * Handles both `{ data: T }` and `{ data: { items: T, total, ... } }` patterns.
 *
 * By default, returns the items array for paginated responses.
 * Use `unwrapPaginated()` to get the full data object with pagination metadata.
 */
export function unwrap<T>(response: unknown): T {
  if (!response || typeof response !== 'object') {
    throw new Error('Invalid API response')
  }
  const obj = response as Record<string, unknown>
  const data = obj.data
  if (!data) {
    throw new Error('No data in API response')
  }
  // If data itself has an items field (paginated), return items
  if (typeof data === 'object' && data !== null && 'items' in (data as Record<string, unknown>)) {
    return (data as Record<string, unknown>).items as T
  }
  return data as T
}

/**
 * Unwrap a paginated response, returning the full data object
 * including pagination metadata (items, total, page, etc.).
 */
export function unwrapPaginated<T>(response: unknown): T {
  if (!response || typeof response !== 'object') {
    throw new Error('Invalid API response')
  }
  const obj = response as Record<string, unknown>
  const data = obj.data
  if (!data) {
    throw new Error('No data in API response')
  }
  return data as T
}

// ---------------------------------------------------------------------------
// 401 auto-refresh: If an access token cookie has expired but the refresh
// token is still valid, we transparently refresh and retry the request.
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

/**
 * Authenticated fetch wrapper with consistent error handling.
 * Automatically includes credentials and Content-Type headers.
 * On 401 responses, attempts a token refresh and retries once.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  }

  // Only set Content-Type for JSON bodies (let FormData set its own boundary)
  if (options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json'
  }

  let response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  })

  // On 401, attempt a token refresh and retry once
  if (response.status === 401) {
    const refreshed = await tryRefreshToken()
    if (refreshed) {
      response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include',
      })
    }
  }

  if (!response.ok) {
    let detail = `API error: ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail || body.message || detail
    } catch {
      // response wasn't JSON, use status-based message
    }

    // If still 401 after refresh, redirect to login
    if (response.status === 401) {
      // Clear any stale auth state
      try { sessionStorage.removeItem('auth-storage') } catch { /* ignore */ }
      window.location.href = '/login'
      throw new Error('Session expired. Please log in again.')
    }

    throw new Error(detail)
  }

  const text = await response.text()
  if (!text) return undefined as T
  const parsed = JSON.parse(text)

  // Unwrap API envelope: { success: true, data: T }
  if (parsed && typeof parsed === 'object' && 'data' in parsed) {
    return parsed.data as T
  }
  return parsed as T
}