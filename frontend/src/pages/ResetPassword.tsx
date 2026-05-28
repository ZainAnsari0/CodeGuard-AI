import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Shield, Eye, EyeOff, Loader, AlertCircle, Lock, CheckCircle } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore } from '../store/authStore'
import { resetPasswordSchema, type ResetPasswordFormData } from '../lib/validation'

export function ResetPassword() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''
  const { resetPassword, isLoading } = useAuthStore()

  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const redirectTimer = useRef<ReturnType<typeof setTimeout>>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { token, newPassword: '' },
  })

  const onSubmit = async (data: ResetPasswordFormData) => {
    setError('')

    if (!token) {
      setError('Invalid or missing reset token. Please request a new password reset link.')
      return
    }

    const result = await resetPassword(data.token, data.newPassword)
    if (result.success) {
      setSuccess(true)
      redirectTimer.current = setTimeout(() => navigate('/login'), 3000)
    } else {
      setError(result.error || 'Password reset failed')
    }
  }

  useEffect(() => {
    return () => {
      if (redirectTimer.current) clearTimeout(redirectTimer.current)
    }
  }, [])

  return (
    <div className="min-h-screen flex auth-bg">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-bg-primary flex-col items-center justify-center p-12">
        <div className="absolute inset-0 grid-pattern opacity-50" />
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-brand-500/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-accent-500/10 rounded-full blur-[100px]" />

        <div className="relative z-10 text-center max-w-md animate-fade-in">
          <div className="mx-auto mb-8 w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan shield-logo">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-text-primary mb-4">
            Reset <span className="gradient-text">Password</span>
          </h1>
          <p className="text-text-secondary text-lg leading-relaxed">
            Create a new secure password for your account.
          </p>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 bg-bg-primary relative">
        <div className="absolute inset-0 grid-pattern opacity-20 pointer-events-none" />

        <div className="w-full max-w-md relative z-10 animate-slide-up">
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br from-brand-400 to-accent-500 shadow-glow-cyan mb-4 shield-logo">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-text-primary">CodeGuard AI</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-text-primary">Set new password</h2>
            <p className="text-text-secondary mt-2">Enter your new password below</p>
          </div>

          <div className="glass-card p-8">
            {error && (
              <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-severity-critical-bg border border-severity-critical/20 animate-fade-in">
                <AlertCircle className="w-5 h-5 text-severity-critical mt-0.5 shrink-0" />
                <p className="text-sm text-severity-critical">{error}</p>
              </div>
            )}

            {success ? (
              <div className="text-center py-6 animate-bounce-in">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-success/10 border-2 border-success/30 mb-5">
                  <CheckCircle className="w-8 h-8 text-success" />
                </div>
                <h3 className="text-xl font-bold text-text-primary mb-2">Password Reset!</h3>
                <p className="text-text-secondary text-sm">
                  Your password has been reset. Redirecting to login...
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <input type="hidden" {...register('token')} />

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      {...register('newPassword')}
                      className={`w-full pl-10 pr-12 py-3 rounded-lg input-glow text-sm text-text-primary placeholder-text-muted ${errors.newPassword ? 'border-severity-critical' : ''}`}
                      placeholder="8+ chars, uppercase, number, symbol"
                    />
                    <button
                      type="button"
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.newPassword && <p className="text-xs text-severity-critical mt-1">{errors.newPassword.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Confirm New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      {...register('confirmPassword')}
                      className={`w-full pl-10 pr-4 py-3 rounded-lg input-glow text-sm text-text-primary placeholder-text-muted ${errors.confirmPassword ? 'border-severity-critical' : ''}`}
                      placeholder="Re-enter your new password"
                    />
                  </div>
                  {errors.confirmPassword && <p className="text-xs text-severity-critical mt-1">{errors.confirmPassword.message}</p>}
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !token}
                  className="w-full py-3 rounded-lg btn-gradient text-sm font-semibold flex items-center justify-center gap-2
                    disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Resetting Password...
                    </>
                  ) : (
                    'Reset Password'
                  )}
                </button>
              </form>
            )}

            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-300 font-medium transition-colors"
              >
                Back to Login
              </Link>
            </div>
          </div>

          <p className="mt-8 text-center text-xs text-text-muted">
            &copy; 2026 CodeGuard AI. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}