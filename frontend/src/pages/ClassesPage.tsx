import { useState } from 'react'
import { useInstructorClasses, useCreateClass, useClassStudents, useRemoveStudent } from '../hooks/useInstructor'
import { GraduationCap, Plus, Users, Copy, Trash2, X, CheckCircle } from 'lucide-react'

export function ClassesPage() {
  const { data: classes, isLoading } = useInstructorClasses()
  const createClass = useCreateClass()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedClass, setSelectedClass] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!name.trim()) return
    await createClass.mutateAsync({ name: name.trim(), description: description.trim() || undefined })
    setName('')
    setDescription('')
    setShowCreate(false)
  }

  const handleCopyCode = (code: string, classId: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(classId)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between animate-slide-up">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/20">
            <GraduationCap className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-display-lg gradient-text">My Classes</h1>
            <p className="text-body-sm text-text-secondary">Manage your classes and student enrollments</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-gradient px-5 py-2.5 rounded-lg text-label-sm flex items-center gap-2 shadow-lg shadow-primary/20"
        >
          <Plus className="w-4 h-4" /> Create Class
        </button>
      </div>

      {/* Create Class Modal */}
      {showCreate && (
        <div className="glass-card p-6 space-y-5 animate-slide-up stagger-1">
          <div className="flex items-center justify-between">
            <h3 className="text-headline-sm text-text-primary">Create New Class</h3>
            <button onClick={() => setShowCreate(false)} className="btn-ghost p-1.5 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-label-sm text-text-muted uppercase tracking-wider mb-2">Class Name</label>
              <input
                type="text"
                placeholder="e.g. CS301 - Secure Coding"
                value={name}
                onChange={e => setName(e.target.value)}
                className="input-glow w-full px-4 py-2.5 rounded-lg text-body-sm text-text-primary placeholder:text-text-muted bg-surface-lowest"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-label-sm text-text-muted uppercase tracking-wider mb-2">Description (optional)</label>
              <textarea
                placeholder="What will students learn in this class?"
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="input-glow w-full px-4 py-2.5 rounded-lg text-body-sm text-text-primary placeholder:text-text-muted bg-surface-lowest resize-none"
                rows={3}
              />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleCreate}
              disabled={createClass.isPending || !name.trim()}
              className="btn-gradient px-5 py-2.5 rounded-lg text-label-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createClass.isPending ? (
                <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Creating...</>
              ) : (
                <><Plus className="w-4 h-4" /> Create Class</>
              )}
            </button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary px-5 py-2.5 rounded-lg text-label-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Classes Grid */}
      {isLoading ? (
        <div className="glass-card p-12 text-center animate-slide-up stagger-1">
          <div className="inline-flex items-center gap-3 text-text-secondary">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            Loading classes...
          </div>
        </div>
      ) : !classes?.length ? (
        <div className="glass-card-hover stat-card-glow p-12 text-center animate-slide-up stagger-1">
          <GraduationCap className="w-16 h-16 mx-auto mb-4 text-text-muted opacity-30" />
          <h3 className="text-headline-sm text-text-primary mb-2">No classes yet</h3>
          <p className="text-body-sm text-text-secondary mb-6">Create your first class to start managing student enrollments.</p>
          <button
            onClick={() => setShowCreate(true)}
            className="btn-gradient px-5 py-2.5 rounded-lg text-label-sm inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Create Your First Class
          </button>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {classes.map((cls, i) => (
            <div
              key={cls.id}
              className={`glass-card-hover stat-card-glow p-5 cursor-pointer animate-slide-up stagger-${i % 6 + 1}`}
              onClick={() => setSelectedClass(selectedClass === cls.id ? null : cls.id)}
            >
              {/* Status + Title */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {cls.is_active ? (
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                      </span>
                    ) : (
                      <span className="inline-flex rounded-full h-2 w-2 bg-amber-400" />
                    )}
                    <span className={`text-label-sm font-medium ${cls.is_active ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {cls.is_active ? 'Active' : 'Draft'}
                    </span>
                  </div>
                  <h3 className="text-body-lg text-text-primary font-semibold truncate">{cls.name}</h3>
                </div>
                <div className="flex items-center gap-1.5 text-text-muted ml-3 shrink-0">
                  <Users className="w-4 h-4" />
                  <span className="text-label-sm font-mono">{cls.student_count}</span>
                </div>
              </div>

              {/* Description */}
              {cls.description && (
                <p className="text-body-sm text-text-secondary mb-4 line-clamp-2">{cls.description}</p>
              )}

              {/* Join Code */}
              <div className="mt-auto pt-3 border-t border-border-light/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-label-sm text-text-muted">Join code</span>
                    <code className="text-label-sm font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">
                      {cls.join_code}
                    </code>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleCopyCode(cls.join_code, cls.id) }}
                    className={`p-1.5 rounded-md transition-all ${
                      copiedCode === cls.id
                        ? 'text-emerald-400 bg-emerald-400/10'
                        : 'text-text-muted hover:text-primary hover:bg-primary/10'
                    }`}
                    title="Copy join code"
                  >
                    {copiedCode === cls.id ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Student List Modal */}
      {selectedClass && <StudentListModal classId={selectedClass} onClose={() => setSelectedClass(null)} />}
    </div>
  )
}

function StudentListModal({ classId, onClose }: { classId: string; onClose: () => void }) {
  const { data: students, isLoading } = useClassStudents(classId)
  const removeStudent = useRemoveStudent()

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in" onClick={onClose}>
      <div className="glass-card p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto animate-slide-up" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-headline-sm text-text-primary">Enrolled Students</h3>
          <button onClick={onClose} className="btn-ghost p-1.5 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : !students?.length ? (
          <div className="text-center py-8">
            <Users className="w-10 h-10 mx-auto mb-3 text-text-muted opacity-30" />
            <p className="text-body-sm text-text-secondary">No students enrolled yet. Share the join code to invite students.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {students.map(s => (
              <div key={s.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-low border border-border-light hover:border-primary/30 transition-all">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500/30 to-cyan-500/30 border border-border-light flex items-center justify-center text-label-sm text-primary font-semibold">
                    {(s.student_name || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-body-md text-text-primary font-medium">{s.student_name || 'Unknown'}</p>
                    <p className="text-label-sm text-text-muted">{s.student_email}</p>
                  </div>
                </div>
                <button
                  onClick={() => removeStudent.mutate({ classId, studentId: s.student_id })}
                  className="btn-ghost text-red-400 hover:!text-red-300 hover:!bg-red-400/10 p-1.5 rounded-lg"
                  title="Remove student"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}