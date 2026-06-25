import { useState } from 'react'
import { GraduationCap, LogIn, LogOut, Users, AlertTriangle, Loader } from 'lucide-react'
import { useMyClasses, useJoinClass, useLeaveClass } from '../hooks/useInstructor'
import { useUIStore } from '../store/uiStore'
import type { EnrolledClass } from '../types'

export function MyClassesPage() {
  const { data: classes, isLoading } = useMyClasses()
  const joinClass = useJoinClass()
  const leaveClass = useLeaveClass()
  const { addToast } = useUIStore()
  const [joinCode, setJoinCode] = useState('')
  const [leavingClassId, setLeavingClassId] = useState<string | null>(null)

  const handleJoin = async () => {
    const code = joinCode.trim()
    if (!code) return
    try {
      await joinClass.mutateAsync(code)
      addToast('Joined class successfully!', 'success')
      setJoinCode('')
    } catch (err: any) {
      const msg = err?.message || err?.body?.message || 'Failed to join class'
      addToast(msg, 'error')
    }
  }

  const handleLeave = async (classId: string, className: string) => {
    setLeavingClassId(classId)
    try {
      await leaveClass.mutateAsync(classId)
      addToast(`Left "${className}"`, 'success')
    } catch {
      addToast('Failed to leave class', 'error')
    } finally {
      setLeavingClassId(null)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center gap-3 animate-slide-up">
        <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/20">
          <GraduationCap className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-display-lg gradient-text">My Classes</h1>
          <p className="text-body-sm text-text-secondary">Join classes and track your enrollments</p>
        </div>
      </div>

      {/* Join Class Card */}
      <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.05s' }}>
        <h2 className="text-headline-sm font-semibold text-on-surface mb-4 flex items-center gap-2">
          <LogIn className="w-4 h-4 text-primary" />
          Join a Class
        </h2>
        <p className="text-body-sm text-text-secondary mb-4">
          Enter the join code provided by your instructor to enroll in a class.
        </p>
        <div className="flex gap-3">
          <input
            type="text"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value)}
            placeholder="Enter join code (e.g., abc123XY)"
            className="flex-1 px-4 py-2.5 rounded-lg bg-surface-high border border-outline-variant text-on-surface text-body-sm
              placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
            onKeyDown={(e) => e.key === 'Enter' && handleJoin()}
          />
          <button
            onClick={handleJoin}
            disabled={!joinCode.trim() || joinClass.isPending}
            className="btn-gradient px-5 py-2.5 rounded-lg text-label-sm font-semibold flex items-center gap-2 shrink-0
              disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20"
          >
            {joinClass.isPending ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            Join
          </button>
        </div>
      </div>

      {/* Enrolled Classes List */}
      <div className="animate-slide-up" style={{ animationDelay: '0.1s' }}>
        <h2 className="text-headline-sm font-semibold text-on-surface mb-4 flex items-center gap-2">
          <GraduationCap className="w-4 h-4 text-primary" />
          Enrolled Classes
        </h2>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card p-5 animate-pulse">
                <div className="h-5 bg-surface-high rounded w-3/4 mb-3" />
                <div className="h-3 bg-surface-high rounded w-full mb-2" />
                <div className="h-3 bg-surface-high rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : !classes || classes.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <GraduationCap className="w-12 h-12 text-on-surface-variant/30 mx-auto mb-4" />
            <h3 className="text-headline-sm text-on-surface mb-2">No classes yet</h3>
            <p className="text-body-sm text-text-secondary">
              Join a class using the join code from your instructor to get started.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {classes.map((cls: EnrolledClass) => (
              <div key={cls.id} className="glass-card p-5 hover:border-primary/30 transition-all duration-200 group">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-body-md font-semibold text-on-surface truncate">{cls.name}</h3>
                    {cls.description && (
                      <p className="text-label-sm text-text-secondary mt-0.5 line-clamp-2">{cls.description}</p>
                    )}
                  </div>
                  <span className="shrink-0 ml-2 px-2 py-0.5 rounded text-label-sm font-medium bg-success/10 text-success border border-success/20">
                    Active
                  </span>
                </div>

                <div className="space-y-2 mt-3">
                  {cls.instructor_name && (
                    <div className="flex items-center gap-2 text-label-sm text-text-secondary">
                      <Users className="w-3.5 h-3.5 text-on-surface-variant" />
                      <span>Instructor: {cls.instructor_name}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-label-sm text-text-secondary">
                    <Users className="w-3.5 h-3.5 text-on-surface-variant" />
                    <span>{cls.student_count} {cls.student_count === 1 ? 'student' : 'students'}</span>
                  </div>
                  {cls.enrolled_at && (
                    <p className="text-label-sm text-on-surface-variant/60">
                      Joined {formatDate(cls.enrolled_at)}
                    </p>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-outline-variant/30">
                  <button
                    onClick={() => handleLeave(cls.id, cls.name)}
                    disabled={leavingClassId === cls.id}
                    className="flex items-center gap-1.5 text-label-sm text-severity-critical/70 hover:text-severity-critical
                      transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {leavingClassId === cls.id ? (
                      <Loader className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <LogOut className="w-3.5 h-3.5" />
                    )}
                    Leave Class
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}