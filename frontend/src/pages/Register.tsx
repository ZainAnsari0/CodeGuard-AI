import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, Eye, EyeOff, Loader, AlertCircle, Lock, Mail, User } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore } from '../store/authStore'
import { registerSchema, type RegisterFormData } from '../lib/validation'
import type { Role } from '../types'

const ROLES: { value: Role; label: string; description: string }[] = [
  { value: 'developer', label: 'Developer', description: 'Scan code and view reports' },
  { value: 'instructor', label: 'Instructor', description: 'Manage classes and track students' },
]

export function Register() {
  const navigate = useNavigate()
  const { register: registerUser, isLoading, error, clearError } = useAuthStore()

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: '', email: '', password: '', confirmPassword: '', role: 'developer' },
  })

  const passwordStrength = (pwd: string): number => {
    let score = 0
    if (pwd.length >= 8) score++
    if (/[A-Z]/.test(pwd)) score++
    if (/[a-z]/.test(pwd)) score++
    if (/[0-9]/.test(pwd)) score++
    if (/[^A-Za-z0-9]/.test(pwd)) score++
    return score
  }

  const watchedPassword = watch('password') || ''
  const watchedRole = watch('role')
  const strength = passwordStrength(watchedPassword)
  const strengthLabels = ['', 'Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong']
  const strengthColors = ['', 'bg-severity-critical', 'bg-severity-high', 'bg-severity-medium', 'bg-success', 'bg-brand-400']

  const onSubmit = async (data: RegisterFormData) => {
    clearError()
    const result = await registerUser(data.email, data.password, data.name, data.role)
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

        <div className="relative z-10 text-center max-w-md animate-fade-in">
          <div className="mx-auto mb-8 w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan shield-logo">
            <Shield className="w-10 h-10 text-white" />
          </div>

          <h1 className="text-4xl font-bold text-text-primary mb-4">
            Join <span className="gradient-text">CodeGuard</span>
          </h1>
          <p className="text-text-secondary text-lg leading-relaxed mb-8">
            Start securing your codebase with AI-powered vulnerability detection and educational insights.
          </p>

          <div className="space-y-4 text-left">
            {[
              { icon: '🔒', title: 'Deep Code Analysis', desc: 'Detect vulnerabilities before deployment' },
              { icon: '🎓', title: 'Learn & Improve', desc: 'Educational insights for every finding' },
              { icon: '⚡', title: 'Instant Feedback', desc: 'Get actionable remediation suggestions' },
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
            <h2 className="text-2xl font-bold text-text-primary">Create account</h2>
            <p className="text-text-secondary mt-2">Get started with CodeGuard AI</p>
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
                <label className="block text-sm font-medium text-text-secondary mb-2">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="text"
                    {...register('name')}
                    className={`w-full pl-10 pr-4 py-3 rounded-lg input-glow text-sm text-text-primary placeholder-text-muted ${errors.name ? 'border-severity-critical' : ''}`}
                    placeholder="John Doe"
                  />
                </div>
                {errors.name && <p className="text-xs text-severity-critical mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Email Address</label>
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
                <label className="block text-sm font-medium text-text-secondary mb-2">Role</label>
                <div className="space-y-2">
                  {ROLES.map((role) => (
                    <label
                      key={role.value}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all duration-200
                        ${watchedRole === role.value
                          ? 'border-brand-500 bg-brand-500/10'
                          : 'border-border-default bg-bg-primary hover:border-text-muted'
                        }`}
                    >
                      <input
                        type="radio"
                        value={role.value}
                        {...register('role')}
                        className="w-4 h-4 text-brand-500 focus:ring-brand-500"
                      />
                      <div>
                        <p className="text-sm font-medium text-text-primary">{role.label}</p>
                        <p className="text-xs text-text-tertiary">{role.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
                {errors.role && <p className="text-xs text-severity-critical mt-1">{errors.role.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    {...register('password')}
                    className={`w-full pl-10 pr-12 py-3 rounded-lg input-glow text-sm text-text-primary placeholder-text-muted ${errors.password ? 'border-severity-critical' : ''}`}
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
                {errors.password && <p className="text-xs text-severity-critical mt-1">{errors.password.message}</p>}
                {watchedPassword && (
                  <div className="mt-2">
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <div
                          key={i}
                          className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                            i <= strength ? strengthColors[strength] : 'bg-bg-tertiary'
                          }`}
                        />
                      ))}
                    </div>
                    <p className={`text-xs mt-1 ${
                      strength >= 4 ? 'text-success' : strength >= 3 ? 'text-severity-medium' : 'text-severity-high'
                    }`}>
                      {strengthLabels[strength] || 'Too short'}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    {...register('confirmPassword')}
                    className={`w-full pl-10 pr-12 py-3 rounded-lg input-glow text-sm text-text-primary placeholder-text-muted ${errors.confirmPassword ? 'border-severity-critical' : ''}`}
                    placeholder="Re-enter your password"
                  />
                  <button
                    type="button"
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.confirmPassword && <p className="text-xs text-severity-critical mt-1">{errors.confirmPassword.message}</p>}
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-lg btn-gradient text-sm font-semibold flex items-center justify-center gap-2
                  disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            <div className="mt-6 flex items-center gap-3">
              <div className="flex-1 h-px bg-border-default" />
              <span className="text-xs text-text-muted">or</span>
              <div className="flex-1 h-px bg-border-default" />
            </div>

            <p className="mt-6 text-center text-sm text-text-secondary">
              Already have an account?{' '}
              <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
                Sign in
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