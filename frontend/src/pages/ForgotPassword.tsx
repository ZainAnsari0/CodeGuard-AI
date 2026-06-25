import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, ArrowLeft, Loader, AlertCircle, Mail, CheckCircle } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore } from '../store/authStore'
import { forgotPasswordSchema, type ForgotPasswordFormData } from '../lib/validation'

export function ForgotPassword() {
  const navigate = useNavigate()
  const { forgotPassword, isLoading } = useAuthStore()
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const redirectTimer = useRef<ReturnType<typeof setTimeout>>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  })

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setError('')
    const result = await forgotPassword(data.email)
    if (result.success) {
      setSuccess(true)
      redirectTimer.current = setTimeout(() => {
        navigate('/login')
      }, 5000)
    } else {
      setError(result.error || 'Failed to send reset email')
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
        <div className="absolute top-1/3 left-1/3 w-72 h-72 bg-brand-500/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/3 right-1/3 w-72 h-72 bg-accent-500/8 rounded-full blur-[100px]" />

        <div className="floating-dot" style={{ top: '25%', left: '30%', animationDelay: '-1.5s' }} />
        <div className="floating-dot" style={{ top: '60%', left: '70%', animationDelay: '-3.5s' }} />

        <div className="relative z-10 text-center max-w-md animate-fade-in">
          <div className="mx-auto mb-8 w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan shield-logo">
            <Shield className="w-10 h-10 text-white" />
          </div>

          <h1 className="text-4xl font-bold text-on-surface mb-4">
            Account <span className="gradient-text">Recovery</span>
          </h1>
          <p className="text-on-surface-variant text-lg leading-relaxed">
            Security is our priority. We&apos;ll help you regain access to your account quickly and safely.
          </p>

          <div className="mt-8 glass-card p-5 rounded-lg text-left space-y-3">
            <h3 className="text-sm font-semibold text-on-surface">Security Tips</h3>
            <ul className="space-y-2">
              {[
                'Use a strong, unique password',
                'Enable two-factor authentication',
                'Never share your login credentials',
              ].map((tip, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-on-surface-variant">
                  <CheckCircle className="w-4 h-4 text-success mt-0.5 shrink-0" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 bg-bg-primary relative">
        <div className="absolute inset-0 grid-pattern opacity-20 pointer-events-none" />

        <div className="w-full max-w-md relative z-10 animate-slide-up">
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br from-brand-400 to-accent-500 shadow-glow-cyan mb-4 shield-logo">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-on-surface">CodeGuard AI</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-on-surface">Forgot Password?</h2>
            <p className="text-on-surface-variant mt-2">No worries, we&apos;ll send you a reset link</p>
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
                <h3 className="text-xl font-bold text-on-surface mb-2">Email Sent!</h3>
                <p className="text-on-surface-variant text-sm">
                  Check your inbox for instructions to reset your password.
                </p>
                <p className="text-xs text-on-surface-variant/60 mt-3">Redirecting to login...</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-on-surface-variant mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/50" />
                    <input
                      type="email"
                      {...register('email')}
                      className={`w-full pl-10 pr-4 py-3 rounded-lg input-glow text-sm text-on-surface placeholder-on-surface-variant/40 ${errors.email ? 'border-severity-critical' : ''}`}
                      placeholder="Enter your email address"
                    />
                  </div>
                  {errors.email && <p className="text-xs text-severity-critical mt-1">{errors.email.message}</p>}
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3 rounded-lg btn-gradient text-sm font-semibold flex items-center justify-center gap-2
                    disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {isLoading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Sending Reset Link...
                    </>
                  ) : (
                    'Send Reset Link'
                  )}
                </button>
              </form>
            )}

            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-300 font-medium transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </div>
          </div>

          <p className="mt-8 text-center text-xs text-on-surface-variant/40">
            &copy; 2026 CodeGuard AI. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}