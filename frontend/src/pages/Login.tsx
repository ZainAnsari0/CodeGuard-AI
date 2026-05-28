import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, Eye, EyeOff, Loader, AlertCircle, Lock, Mail } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore } from '../store/authStore'
import { loginSchema, type LoginFormData } from '../lib/validation'

export function Login() {
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)

  const { login, isLoading, error, clearError, loginAttempted, checkAuthStatus } = useAuthStore()

  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  useEffect(() => {
    if (loginAttempted) {
      const checkAuth = async () => {
        const isAuthenticated = await checkAuthStatus()
        if (isAuthenticated) {
          navigate('/dashboard')
        }
      }
      checkAuth()
    }
  }, [loginAttempted, navigate, checkAuthStatus])

  const onSubmit = async (data: LoginFormData) => {
    clearError()
    const result = await login(data.email, data.password)
    if (result.success) {
      navigate('/dashboard')
    }
  }

  return (
    <div className="min-h-screen flex auth-bg">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-bg-primary flex-col items-center justify-center p-12">
        <div className="absolute inset-0 grid-pattern opacity-50" />
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-brand-500/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-accent-500/10 rounded-full blur-[100px]" />

        <div className="floating-dot" style={{ top: '15%', left: '20%', animationDelay: '0s' }} />
        <div className="floating-dot" style={{ top: '70%', left: '75%', animationDelay: '-2s' }} />
        <div className="floating-dot" style={{ top: '40%', left: '85%', animationDelay: '-4s' }} />

        <div className="relative z-10 text-center max-w-md animate-fade-in">
          <div className="mx-auto mb-8 w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan shield-logo">
            <Shield className="w-10 h-10 text-white" />
          </div>

          <h1 className="text-4xl font-bold text-text-primary mb-4">
            Secure Your <span className="gradient-text">Code</span>
          </h1>
          <p className="text-text-secondary text-lg leading-relaxed mb-8">
            AI-powered vulnerability detection that protects your codebase from security threats before they reach production.
          </p>

          <div className="space-y-4 text-left">
            {[
              { icon: '🔍', title: 'Deep Code Analysis', desc: 'Scan every file for vulnerabilities' },
              { icon: '🛡️', title: 'Real-time Protection', desc: 'Continuous monitoring and alerts' },
              { icon: '📊', title: 'Detailed Reports', desc: 'Actionable insights with fix suggestions' },
            ].map((feature, i) => (
              <div key={i} className="flex items-start gap-3 glass-card p-3 rounded-lg">
                <span className="text-lg mt-0.5">{feature.icon}</span>
                <div>
                  <p className="text-sm font-medium text-text-primary">{feature.title}</p>
                  <p className="text-xs text-text-tertiary">{feature.desc}</p>
                </div>
              </div>
            ))}
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
            <h1 className="text-2xl font-bold text-text-primary">CodeGuard AI</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-text-primary">Welcome back</h2>
            <p className="text-text-secondary mt-2">Sign in to your account to continue</p>
          </div>

          <div className="glass-card p-8">
            {error && (
              <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-severity-critical-bg border border-severity-critical/20 animate-fade-in">
                <AlertCircle className="w-5 h-5 text-severity-critical mt-0.5 shrink-0" />
                <p className="text-sm text-severity-critical">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="email"
                    {...register('email')}
                    className={`w-full pl-10 pr-4 py-3 rounded-lg input-glow text-sm text-text-primary placeholder-text-muted ${errors.email ? 'border-severity-critical' : ''}`}
                    placeholder="you@company.com"
                  />
                </div>
                {errors.email && <p className="text-xs text-severity-critical mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    {...register('password')}
                    className={`w-full pl-10 pr-12 py-3 rounded-lg input-glow text-sm text-text-primary placeholder-text-muted ${errors.password ? 'border-severity-critical' : ''}`}
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-xs text-severity-critical mt-1">{errors.password.message}</p>}
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={() => setRememberMe(!rememberMe)}
                    className="w-4 h-4 rounded border-border-default bg-bg-primary text-brand-500
                      focus:ring-brand-500 focus:ring-offset-bg-primary focus:ring-offset-0"
                  />
                  <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
                    Remember me
                  </span>
                </label>
                <Link
                  to="/forgot-password"
                  className="text-sm text-brand-400 hover:text-brand-300 font-medium transition-colors"
                >
                  Forgot password?
                </Link>
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
                    Authenticating...
                  </>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            <div className="mt-6 flex items-center gap-3">
              <div className="flex-1 h-px bg-border-default" />
              <span className="text-xs text-text-muted">or</span>
              <div className="flex-1 h-px bg-border-default" />
            </div>

            <p className="mt-6 text-center text-sm text-text-secondary">
              Don&apos;t have an account?{' '}
              <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
                Create account
              </Link>
            </p>
          </div>

          <p className="mt-8 text-center text-xs text-text-muted">
            &copy; 2026 CodeGuard AI. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}