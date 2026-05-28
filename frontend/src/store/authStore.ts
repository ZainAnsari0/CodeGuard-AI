import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'
import type { AuthStore, Role, User } from '../types'
import { API_BASE_URL, unwrap } from '../lib/api'

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // State
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      loginAttempted: false,

      // Role helpers
      isDeveloper: () => get().user?.role === 'developer',
      isInstructor: () => get().user?.role === 'instructor',
      isAdmin: () => get().user?.role === 'admin',
      hasRole: (role: string) => get().user?.role === role,

      // Actions
      setUser: (user: User) => set({ user, isAuthenticated: !!user, loginAttempted: true }),
      setError: (error: string | null) => set({ error }),
      clearError: () => set({ error: null }),
      setLoading: (isLoading: boolean) => set({ isLoading }),

      // Login — tokens are set as httpOnly cookies by the backend
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null, loginAttempted: true })

        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            credentials: 'include',
            body: new URLSearchParams({ username: email, password }),
          })

          const raw = await response.json()

          if (!response.ok) {
            const errMsg = (raw as Record<string, unknown>).detail || (raw as Record<string, unknown>).message || 'Login failed'
            throw new Error(errMsg as string)
          }

          const data = unwrap<{ user: User }>(raw)

          set({
            user: data.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })

          return { success: true, user: data.user }
        } catch (error: unknown) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Login failed',
          })
          return { success: false, error: error instanceof Error ? error.message : 'Login failed' }
        }
      },

      // Register — tokens are set as httpOnly cookies by the backend
      register: async (email: string, password: string, name: string, role: Role | string = 'developer') => {
        set({ isLoading: true, error: null })

        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ email, password, full_name: name, role }),
          })

          const raw = await response.json()

          if (!response.ok) {
            const rawObj = raw as Record<string, unknown>
            const errMsg = rawObj.detail || rawObj.message || 'Registration failed'
            if (rawObj.errors && Array.isArray(rawObj.errors)) {
              throw new Error((rawObj.errors as Array<{ message: string }>).map(e => e.message).join(', '))
            }
            throw new Error(errMsg as string)
          }

          const data = unwrap<{ user: User }>(raw)

          set({
            user: data.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })

          return { success: true, user: data.user }
        } catch (error: unknown) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Registration failed',
          })
          return { success: false, error: error instanceof Error ? error.message : 'Registration failed' }
        }
      },

      // Logout
      logout: async () => {
        set({ isLoading: true })

        try {
          await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
            method: 'POST',
            credentials: 'include',
          })
        } catch {
          // Ignore API errors on logout
        }

        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        })
      },

      // Refresh token — cookies are sent automatically
      refreshAuthToken: async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
            method: 'POST',
            credentials: 'include',
          })

          if (!response.ok) {
            throw new Error('Token refresh failed')
          }

          return { success: true }
        } catch {
          set({
            user: null,
            isAuthenticated: false,
          })
          return { success: false, error: 'Token refresh failed' }
        }
      },

      // Check auth status — rely on cookies, with recursion guard
      checkAuthStatus: async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
            method: 'GET',
            credentials: 'include',
          })

          if (response.ok) {
            const raw = await response.json()
            const userData = unwrap<Record<string, unknown>>(raw)
            const user = (userData.user || userData) as User
            set({ user, isAuthenticated: true, isLoading: false })
            return true
          }
        } catch {
          // Fall through to refresh
        }

        // Try refreshing the token (one attempt only — no recursion)
        const refreshResult = await get().refreshAuthToken()
        if (refreshResult?.success) {
          try {
            const verifyResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
              method: 'GET',
              credentials: 'include',
            })
            if (verifyResponse.ok) {
              const raw = await verifyResponse.json()
              const userData = unwrap<Record<string, unknown>>(raw)
              const user = (userData.user || userData) as User
              set({ user, isAuthenticated: true, isLoading: false })
              return true
            }
          } catch {
            // Refresh succeeded but verification failed
          }
        }

        set({ isAuthenticated: false, isLoading: false })
        return false
      },

      // Forgot password
      forgotPassword: async (email: string) => {
        set({ isLoading: true, error: null })

        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ email }),
          })

          const raw = await response.json()

          set({ isLoading: false })
          return { success: true, message: (raw as Record<string, unknown>).message as string || 'If an account with that email exists, a reset link has been sent.' }
        } catch {
          set({ isLoading: false })
          return { success: true, message: 'If an account with that email exists, a reset link has been sent.' }
        }
      },

      // Reset password
      resetPassword: async (token: string, newPassword: string) => {
        set({ isLoading: true, error: null })

        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ token, new_password: newPassword }),
          })

          const raw = await response.json()

          if (!response.ok) {
            const rawObj = raw as Record<string, unknown>
            const errMsg = rawObj.detail || rawObj.message || 'Password reset failed'
            if (rawObj.errors && Array.isArray(rawObj.errors)) {
              throw new Error((rawObj.errors as Array<{ message: string }>).map(e => e.message).join(', '))
            }
            throw new Error(errMsg as string)
          }

          set({ isLoading: false })
          return { success: true, message: 'Password has been reset successfully.' }
        } catch (error: unknown) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Password reset failed',
          })
          return { success: false, error: error instanceof Error ? error.message : 'Password reset failed' }
        }
      },
    }),
    {
      name: 'auth-store',
      storage: createJSONStorage(() => sessionStorage),
      // Only persist minimal info — NOT tokens (cookies handle that)
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: !!state.user,
        loginAttempted: state.loginAttempted,
      }),
    }
  )
)