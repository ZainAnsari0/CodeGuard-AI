import { useState } from 'react'
import { useInstructorClasses, useCreateClass, useClassStudents, useRemoveStudent } from '../hooks/useInstructor'
import { GraduationCap, Plus, Users, Copy, Trash2, ChevronRight } from 'lucide-react'

export function ClassesPage() {
  const { data: classes, isLoading } = useInstructorClasses()
  const createClass = useCreateClass()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedClass, setSelectedClass] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!name.trim()) return
    await createClass.mutateAsync({ name: name.trim(), description: description.trim() || undefined })
    setName('')
    setDescription('')
    setShowCreate(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">My Classes</h1>
          <p className="text-text-secondary mt-1">Manage your classes and student enrollments</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Class
        </button>
      </div>

      {showCreate && (
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-lg font-semibold text-text-primary">Create New Class</h3>
          <input
            type="text" placeholder="Class name" value={name} onChange={e => setName(e.target.value)}
            className="input-field w-full"
          />
          <textarea
            placeholder="Description (optional)" value={description} onChange={e => setDescription(e.target.value)}
            className="input-field w-full" rows={3}
          />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="btn-primary" disabled={createClass.isPending}>
              {createClass.isPending ? 'Creating...' : 'Create'}
            </button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="glass-card p-8 text-center text-text-secondary">Loading classes...</div>
      ) : !classes?.length ? (
        <div className="glass-card p-8 text-center text-text-secondary">
          <GraduationCap className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No classes yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {classes.map(cls => (
            <div key={cls.id} className="glass-card p-5 hover:border-primary/40 transition-colors cursor-pointer"
              onClick={() => setSelectedClass(selectedClass === cls.id ? null : cls.id)}>
              <div className="flex items-start justify-between">
                <h3 className="font-semibold text-text-primary">{cls.name}</h3>
                <span className="flex items-center gap-1 text-sm text-text-muted">
                  <Users className="w-4 h-4" /> {cls.student_count}
                </span>
              </div>
              {cls.description && <p className="text-sm text-text-secondary mt-2 line-clamp-2">{cls.description}</p>}
              <div className="mt-3 flex items-center gap-2 text-xs text-text-muted">
                <span className="bg-surface-3 px-2 py-0.5 rounded">Join code: {cls.join_code}</span>
                <button onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(cls.join_code) }}
                  className="text-primary hover:text-primary-light" title="Copy join code">
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
              <ChevronRight className="w-4 h-4 text-text-muted mt-2" />
            </div>
          ))}
        </div>
      )}

      {selectedClass && <StudentListModal classId={selectedClass} onClose={() => setSelectedClass(null)} />}
    </div>
  )
}

function StudentListModal({ classId, onClose }: { classId: string; onClose: () => void }) {
  const { data: students, isLoading } = useClassStudents(classId)
  const removeStudent = useRemoveStudent()

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="glass-card p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-text-primary">Enrolled Students</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">&times;</button>
        </div>
        {isLoading ? (
          <p className="text-text-secondary">Loading...</p>
        ) : !students?.length ? (
          <p className="text-text-secondary text-center py-4">No students enrolled yet. Share the join code.</p>
        ) : (
          <div className="space-y-2">
            {students.map(s => (
              <div key={s.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-2">
                <div>
                  <p className="text-text-primary font-medium">{s.student_name || 'Unknown'}</p>
                  <p className="text-text-muted text-sm">{s.student_email}</p>
                </div>
                <button onClick={() => removeStudent.mutate({ classId, studentId: s.student_id })}
                  className="text-red-400 hover:text-red-300 p-1" title="Remove student">
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