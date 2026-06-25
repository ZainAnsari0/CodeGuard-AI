import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, Eye, EyeOff, Loader, AlertCircle, Lock, Mail, User, Code, GraduationCap } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthStore } from '../store/authStore'
import { registerSchema, type RegisterFormData } from '../lib/validation'
import type { Role } from '../types'

const ROLES: { value: Role; label: string; description: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { value: 'developer', label: 'Developer', description: 'Scan code and view reports', icon: Code },
  { value: 'instructor', label: 'Instructor', description: 'Manage classes and track students', icon: GraduationCap },
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
    <div className="min-h-screen flex">
      {/* ─── Left Panel: Branding with background image ─── */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden flex-col items-center justify-center p-12"
        style={{ background: 'linear-gradient(135deg, #0b1326 0%, #171f33 50%, #1e293b 100%)' }}>
        <div className="absolute inset-0 bg-grid-pattern opacity-30" />
        <div className="absolute top-1/3 left-1/4 w-80 h-80 rounded-full bg-brand-500/10 blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-72 h-72 rounded-full bg-accent-500/8 blur-[120px]" />

        <div className="floating-dot" style={{ top: '20%', left: '30%', animationDelay: '0s' }} />
        <div className="floating-dot" style={{ top: '65%', left: '70%', animationDelay: '-2s' }} />
        <div className="floating-dot" style={{ top: '45%', left: '80%', animationDelay: '-4s' }} />

        <div className="relative z-10 text-center max-w-md" style={{ animation: 'fade-in 0.6s ease-out' }}>
          <div className="mx-auto mb-8 w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan shield-logo">
            <Shield className="w-10 h-10 text-white" />
          </div>

          <h1 className="text-display-xl font-bold text-on-surface mb-4">
            Join <span className="gradient-text">CodeGuard</span>
          </h1>
          <p className="text-body-lg text-on-surface-variant leading-relaxed mb-8">
            Start securing your codebase with AI-powered vulnerability detection and educational insights.
          </p>

          <div className="space-y-4 text-left">
            {[
              { icon: '🔒', title: 'Deep Code Analysis', desc: 'Detect vulnerabilities before deployment' },
              { icon: '🎓', title: 'Learn & Improve', desc: 'Educational insights for every finding' },
              { icon: '⚡', title: 'Instant Feedback', desc: 'Get actionable remediation suggestions' },
            ].map((feature, i) => (
              <div key={i} className="flex items-start gap-3 glass-panel p-4 rounded-lg hover:border-primary/20 transition-all duration-200" style={{ animationDelay: `${i * 0.1}s` }}>
                <span className="text-lg mt-0.5">{feature.icon}</span>
                <div>
                  <p className="text-body-sm font-medium text-on-surface">{feature.title}</p>
                  <p className="text-label-sm text-on-surface-variant">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Right Panel: Register Form ─── */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 bg-surface relative">
        <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none" />

        <div className="w-full max-w-md relative z-10" style={{ animation: 'slide-up 0.5s ease-out' }}>
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br from-brand-400 to-accent-500 shadow-glow-cyan mb-4 shield-logo">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-headline-md font-bold text-on-surface">CodeGuard AI</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-display-lg font-bold text-on-surface">Create account</h2>
            <p className="text-body-md text-on-surface-variant mt-2">Get started with CodeGuard AI</p>
          </div>

          <div className="glass-panel p-8">
            {error && (
              <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-severity-critical-bg border border-severity-critical/20 animate-fade-in">
                <AlertCircle className="w-5 h-5 text-severity-critical mt-0.5 shrink-0" />
                <p className="text-body-sm text-severity-critical">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label className="block text-label-md font-medium text-on-surface-variant mb-2">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/50" />
                  <input
                    type="text"
                    {...register('name')}
                    className={`w-full pl-10 pr-4 py-3 rounded-lg input-glow text-body-md text-on-surface placeholder-on-surface-variant/40 ${errors.name ? 'border-severity-critical' : ''}`}
                    placeholder="John Doe"
                  />
                </div>
                {errors.name && <p className="text-label-sm text-severity-critical mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <label className="block text-label-md font-medium text-on-surface-variant mb-2">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/50" />
                  <input
                    type="email"
                    {...register('email')}
                    className={`w-full pl-10 pr-4 py-3 rounded-lg input-glow text-body-md text-on-surface placeholder-on-surface-variant/40 ${errors.email ? 'border-severity-critical' : ''}`}
                    placeholder="you@company.com"
                  />
                </div>
                {errors.email && <p className="text-label-sm text-severity-critical mt-1">{errors.email.message}</p>}
              </div>

              {/* ─── Role Selection Cards (Stitch design) ─── */}
              <div>
                <label className="block text-label-md font-medium text-on-surface-variant mb-2">I am a</label>
                <div className="grid grid-cols-2 gap-3">
                  {ROLES.map((role) => {
                    const Icon = role.icon
                    const isSelected = watchedRole === role.value
                    return (
                      <label
                        key={role.value}
                        className={`flex flex-col items-center gap-2 p-4 rounded-xl cursor-pointer transition-all duration-200
                          ${isSelected
                            ? 'glass-panel border-primary/50 shadow-glow-cyan-sm'
                            : 'border border-outline-variant/50 bg-surface-low hover:border-outline hover:bg-surface-container'
                          }`}
                      >
                        <input
                          type="radio"
                          value={role.value}
                          {...register('role')}
                          className="sr-only"
                        />
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors duration-200
                          ${isSelected ? 'bg-gradient-to-br from-brand-400 to-accent-500 text-white' : 'bg-surface-high text-on-surface-variant'}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <p className={`text-body-sm font-medium ${isSelected ? 'text-primary' : 'text-on-surface-variant'}`}>{role.label}</p>
                        <p className="text-label-sm text-on-surface-variant/60 text-center">{role.description}</p>
                      </label>
                    )
                  })}
                </div>
                {errors.role && <p className="text-label-sm text-severity-critical mt-1">{errors.role.message}</p>}
              </div>

              <div>
                <label className="block text-label-md font-medium text-on-surface-variant mb-2">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/50" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    {...register('password')}
                    className={`w-full pl-10 pr-12 py-3 rounded-lg input-glow text-body-md text-on-surface placeholder-on-surface-variant/40 ${errors.password ? 'border-severity-critical' : ''}`}
                    placeholder="8+ chars, uppercase, number, symbol"
                  />
                  <button
                    type="button"
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant/50 hover:text-on-surface-variant transition-colors"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-label-sm text-severity-critical mt-1">{errors.password.message}</p>}
                {/* Password strength meter (Stitch design) */}
                {watchedPassword && (
                  <div className="mt-2">
                    <div className="flex gap-1.5">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <div
                          key={i}
                          className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                            i <= strength ? strengthColors[strength] : 'bg-surface-high'
                          }`}
                        />
                      ))}
                    </div>
                    <p className={`text-label-sm mt-1 ${
                      strength >= 4 ? 'text-success' : strength >= 3 ? 'text-severity-medium' : 'text-severity-high'
                    }`}>
                      {strengthLabels[strength] || 'Too short'}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-label-md font-medium text-on-surface-variant mb-2">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/50" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    {...register('confirmPassword')}
                    className={`w-full pl-10 pr-12 py-3 rounded-lg input-glow text-body-md text-on-surface placeholder-on-surface-variant/40 ${errors.confirmPassword ? 'border-severity-critical' : ''}`}
                    placeholder="Re-enter your password"
                  />
                  <button
                    type="button"
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant/50 hover:text-on-surface-variant transition-colors"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.confirmPassword && <p className="text-label-sm text-severity-critical mt-1">{errors.confirmPassword.message}</p>}
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-lg btn-gradient text-body-md font-semibold flex items-center justify-center gap-2
                  disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
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
              <div className="flex-1 h-px bg-outline-variant/50" />
              <span className="text-label-sm text-on-surface-variant/60">or</span>
              <div className="flex-1 h-px bg-outline-variant/50" />
            </div>

            <p className="mt-6 text-center text-body-sm text-on-surface-variant">
              Already have an account?{' '}
              <Link to="/login" className="text-primary hover:text-brand-300 font-medium transition-colors">
                Sign in
              </Link>
            </p>
          </div>

          <p className="mt-8 text-center text-label-sm text-on-surface-variant/40">
            &copy; 2026 CodeGuard AI. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}