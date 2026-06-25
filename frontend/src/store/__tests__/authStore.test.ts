import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore } from '../authStore'

describe('AuthStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      loginAttempted: false,
    })
    localStorage.clear()
  })

  describe('initial state', () => {
    it('starts unauthenticated', () => {
      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
    })
  })

  describe('role helpers', () => {
    it('isDeveloper returns true when user role is developer', () => {
      useAuthStore.setState({
        user: { id: '1', email: 'dev@test.com', role: 'developer', is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null },
        isAuthenticated: true,
      })
      expect(useAuthStore.getState().isDeveloper()).toBe(true)
      expect(useAuthStore.getState().isAdmin()).toBe(false)
    })

    it('isAdmin returns true when user role is admin', () => {
      useAuthStore.setState({
        user: { id: '1', email: 'admin@test.com', role: 'admin', is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null },
        isAuthenticated: true,
      })
      expect(useAuthStore.getState().isAdmin()).toBe(true)
      expect(useAuthStore.getState().isDeveloper()).toBe(false)
    })

    it('hasRole checks specific role', () => {
      useAuthStore.setState({
        user: { id: '1', email: 'instr@test.com', role: 'instructor', is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null },
        isAuthenticated: true,
      })
      expect(useAuthStore.getState().hasRole('instructor')).toBe(true)
      expect(useAuthStore.getState().hasRole('admin')).toBe(false)
    })

    it('role helpers return false when user is null', () => {
      useAuthStore.setState({ user: null })
      expect(useAuthStore.getState().isDeveloper()).toBe(false)
      expect(useAuthStore.getState().isInstructor()).toBe(false)
      expect(useAuthStore.getState().isAdmin()).toBe(false)
    })
  })

  describe('setUser', () => {
    it('sets user and updates isAuthenticated', () => {
      const user = { id: '1', email: 'test@test.com', role: 'developer' as const, is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null }
      useAuthStore.getState().setUser(user)
      expect(useAuthStore.getState().user).toEqual(user)
      expect(useAuthStore.getState().isAuthenticated).toBe(true)
      expect(useAuthStore.getState().loginAttempted).toBe(true)
    })
  })

  describe('setError / clearError', () => {
    it('sets and clears errors', () => {
      useAuthStore.getState().setError('Test error')
      expect(useAuthStore.getState().error).toBe('Test error')
      useAuthStore.getState().clearError()
      expect(useAuthStore.getState().error).toBeNull()
    })
  })

  describe('login', () => {
    it('handles successful login', async () => {
      const mockUser = { id: '1', email: 'test@test.com', role: 'developer', full_name: null, name: null, is_active: true, is_superuser: false, last_login: null, created_at: null, updated_at: null }
      globalThis.fetch = vi.fn().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: { user: mockUser },
          }),
          { status: 200 }
        )
      )

      const result = await useAuthStore.getState().login('test@test.com', 'password123')

      expect(result.success).toBe(true)
      expect(useAuthStore.getState().isAuthenticated).toBe(true)
      expect(useAuthStore.getState().user?.email).toBe('test@test.com')
    })

    it('handles login failure', async () => {
      globalThis.fetch = vi.fn().mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Invalid credentials' }), { status: 400 })
      )

      const result = await useAuthStore.getState().login('test@test.com', 'wrong')

      expect(result.success).toBe(false)
      expect(useAuthStore.getState().error).toBe('Invalid credentials')
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
    })

    it('handles network error during login', async () => {
      globalThis.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'))

      const result = await useAuthStore.getState().login('test@test.com', 'password')

      expect(result.success).toBe(false)
      expect(useAuthStore.getState().error).toBe('Network error')
    })
  })

  describe('logout', () => {
    it('clears auth state on logout', async () => {
      useAuthStore.setState({
        user: { id: '1', email: 'test@test.com', role: 'developer', is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null },
        isAuthenticated: true,
      })

      globalThis.fetch = vi.fn().mockResolvedValueOnce(
        new Response(JSON.stringify({}), { status: 200 })
      )

      await useAuthStore.getState().logout()

      expect(useAuthStore.getState().user).toBeNull()
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
    })
  })
})