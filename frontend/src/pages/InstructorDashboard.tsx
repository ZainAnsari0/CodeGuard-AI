import { useInstructorClasses } from '../hooks/useInstructor'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import { GraduationCap, Users, Plus, BookOpen, ArrowRight, Clipboard } from 'lucide-react'
import { StatCard } from '../components/dashboard/StatCard'
import { SkeletonStatCard } from '../components/ui/Skeleton'

export function InstructorDashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { data: classes, isLoading } = useInstructorClasses()

  const firstName = user?.full_name?.split(' ')[0] || 'Instructor'
  const greetingHour = new Date().getHours()
  const greeting = greetingHour < 12 ? 'Good morning' : greetingHour < 18 ? 'Good afternoon' : 'Good evening'

  const totalClasses = classes?.length || 0
  const totalStudents = classes?.reduce((acc, cls) => acc + (cls.student_count || 0), 0) || 0

  const stats = [
    {
      title: 'Total Classes',
      value: totalClasses,
      icon: GraduationCap,
      color: 'from-accent-400 to-accent-600',
      glowColor: 'shadow-glow-violet',
    },
    {
      title: 'Enrolled Students',
      value: totalStudents,
      icon: Users,
      color: 'from-brand-400 to-brand-600',
      glowColor: 'shadow-glow-cyan-sm',
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ─── Header ─── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-display-xl font-bold text-on-surface">
            {greeting}, <span className="gradient-text">{firstName}</span>
          </h1>
          <p className="text-body-md text-on-surface-variant mt-1">Here&apos;s an overview of your active classes and student progress.</p>
        </div>
        <button
          onClick={() => navigate('/classes')}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg btn-gradient text-body-md font-semibold shrink-0 shadow-glow-cyan-sm"
        >
          <Plus className="w-4 h-4" />
          Manage Classes
        </button>
      </div>

      {/* ─── Stats Grid ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-4xl">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => <SkeletonStatCard key={i} />)
        ) : (
          stats.map((stat, index) => (
            <StatCard
              key={stat.title}
              title={stat.title}
              value={stat.value}
              change=""
              trend="up"
              icon={stat.icon}
              color={stat.color}
              glowColor={stat.glowColor}
              index={index}
            />
          ))
        )}
      </div>

      {/* ─── Main Content Layout ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left/Middle: My Classes List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
              <h2 className="text-headline-sm font-bold text-on-surface flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-accent-400" />
                Active Classes
              </h2>
              <button
                onClick={() => navigate('/classes')}
                className="text-label-md text-brand-400 hover:text-brand-300 font-semibold transition-colors flex items-center gap-1"
              >
                View All <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {isLoading ? (
              <div className="py-8 text-center text-on-surface-variant">Loading classes...</div>
            ) : !classes?.length ? (
              <div className="py-12 text-center space-y-3">
                <GraduationCap className="w-12 h-12 text-on-surface-variant/40 mx-auto" />
                <p className="text-body-md text-on-surface-variant">No classes created yet.</p>
                <button
                  onClick={() => navigate('/classes')}
                  className="px-4 py-2 rounded-lg bg-surface-high text-on-surface text-label-md font-semibold hover:bg-surface-highest transition-colors"
                >
                  Create Your First Class
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {classes.slice(0, 4).map((cls) => (
                  <div
                    key={cls.id}
                    onClick={() => navigate(`/classes/${cls.id}/metrics`)}
                    className="glass-card-hover border border-outline-variant/40 p-4 rounded-xl cursor-pointer flex flex-col justify-between space-y-3 transition-all"
                  >
                    <div>
                      <h3 className="text-body-lg font-bold text-on-surface truncate">{cls.name}</h3>
                      {cls.description && (
                        <p className="text-body-sm text-on-surface-variant line-clamp-2 mt-1">{cls.description}</p>
                      )}
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t border-outline-variant/30 text-label-sm">
                      <div className="flex items-center gap-1.5 text-on-surface-variant">
                        <Users className="w-4 h-4 text-brand-400" />
                        <span>{cls.student_count} Students</span>
                      </div>
                      <div className="flex items-center gap-1 bg-surface-high/60 px-2 py-0.5 rounded font-mono text-brand-400">
                        <Clipboard className="w-3.5 h-3.5" />
                        <span>{cls.join_code}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar: Quick Actions */}
        <div className="space-y-4">
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-headline-sm font-bold text-on-surface border-b border-outline-variant/30 pb-3 flex items-center gap-2">
              <Clipboard className="w-5 h-5 text-brand-400" />
              Quick Actions
            </h2>
            <div className="space-y-2">
              <button
                onClick={() => navigate('/classes')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-surface-high/40 hover:bg-surface-high/80 border border-outline-variant/20 hover:border-brand-400/40 text-left transition-all"
              >
                <div>
                  <p className="text-body-md font-semibold text-on-surface">Manage Classes</p>
                  <p className="text-label-sm text-on-surface-variant">Create classes and view join codes</p>
                </div>
                <ArrowRight className="w-5 h-5 text-on-surface-variant" />
              </button>

              <button
                onClick={() => navigate('/students')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-surface-high/40 hover:bg-surface-high/80 border border-outline-variant/20 hover:border-brand-400/40 text-left transition-all"
              >
                <div>
                  <p className="text-body-md font-semibold text-on-surface">Track Student Progress</p>
                  <p className="text-label-sm text-on-surface-variant">View student list and audit records</p>
                </div>
                <ArrowRight className="w-5 h-5 text-on-surface-variant" />
              </button>

              <button
                onClick={() => navigate('/knowledge-base')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-surface-high/40 hover:bg-surface-high/80 border border-outline-variant/20 hover:border-brand-400/40 text-left transition-all"
              >
                <div>
                  <p className="text-body-md font-semibold text-on-surface">Browse Knowledge Base</p>
                  <p className="text-label-sm text-on-surface-variant">Access security reference material</p>
                </div>
                <ArrowRight className="w-5 h-5 text-on-surface-variant" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
