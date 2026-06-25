import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore } from '../../store/authStore'

describe('Login Page (via AuthStore)', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      loginAttempted: false,
    })
  })

  it('sets error on failed login', async () => {
    globalThis.fetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Invalid credentials' }), { status: 400 })
    )

    const result = await useAuthStore.getState().login('bad@test.com', 'wrongpass')
    expect(result.success).toBe(false)
    expect(useAuthStore.getState().error).toBe('Invalid credentials')
  })

  it('sets loading state during login', async () => {
    let resolveLogin: (value: unknown) => void
    const pendingPromise = new Promise((resolve) => { resolveLogin = resolve })

    globalThis.fetch = vi.fn().mockReturnValueOnce(pendingPromise)

    const loginPromise = useAuthStore.getState().login('test@test.com', 'password')
    expect(useAuthStore.getState().isLoading).toBe(true)

    resolveLogin!(
      new Response(
        JSON.stringify({
          user: { id: '1', email: 'test@test.com', role: 'developer' },
          access_token: 'token',
          refresh_token: 'refresh',
        }),
        { status: 200 }
      )
    )

    await loginPromise
    expect(useAuthStore.getState().isLoading).toBe(false)
  })

  it('clears error state', () => {
    useAuthStore.setState({ error: 'Some error' })
    useAuthStore.getState().clearError()
    expect(useAuthStore.getState().error).toBeNull()
  })
})