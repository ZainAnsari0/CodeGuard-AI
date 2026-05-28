/**
 * Shared API utilities for CodeGuard frontend.
 * Eliminates duplicated unwrap/apiFetch/API_BASE_URL across hooks and pages.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export { API_BASE_URL }

/**
 * Unwrap a paginated or data-wrapped API response.
 * Handles both `{ data: T }` and `{ data: { items: T } }` patterns.
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
 * Authenticated fetch wrapper with consistent error handling.
 * Automatically includes credentials and Content-Type headers.
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

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    let detail = `API error: ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail || body.message || detail
    } catch {
      // response wasn't JSON, use status-based message
    }
    throw new Error(detail)
  }

  const text = await response.text()
  if (!text) return undefined as T
  return JSON.parse(text)
}