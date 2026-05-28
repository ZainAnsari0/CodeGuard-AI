import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { Shield } from 'lucide-react'
import type { ProtectedRouteProps } from '../../types'

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="flex flex-col items-center gap-6 animate-fade-in">
          <div className="relative">
            <div className="absolute inset-0 -m-3 rounded-full bg-brand-500/10 animate-pulse" />
            <div className="absolute inset-0 -m-2 rounded-full border-2 border-transparent border-t-brand-400 border-r-accent-400 animate-spin"
              style={{ animationDuration: '1.5s' }}
            />
            <div className="relative z-10 w-16 h-16 rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center shadow-glow-cyan shield-logo">
              <Shield className="w-8 h-8 text-white" />
            </div>
          </div>

          <div className="text-center">
            <p className="text-text-primary font-medium text-sm">Authenticating</p>
            <p className="text-text-tertiary text-xs mt-1">Verifying your session...</p>
          </div>

          <div className="flex gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && allowedRoles.length > 0) {
    if (!allowedRoles.includes(user?.role as 'developer' | 'instructor' | 'admin')) {
      return <Navigate to="/dashboard" replace />
    }
  }

  return <>{children}</>
}