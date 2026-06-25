import { useState } from 'react'
import { useAdminUsers, useUpdateUser, useDeactivateUser } from '../hooks/useAdmin'
import { Users, Search, Shield, UserX, CheckCircle, ChevronLeft, ChevronRight, ToggleLeft, ToggleRight } from 'lucide-react'

export function AdminUsersPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string | undefined>(undefined)
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const { data, isLoading } = useAdminUsers(page, 20, roleFilter, search || undefined)
  const updateUser = useUpdateUser()
  const deactivateUser = useDeactivateUser()

  const handleRoleChange = async (userId: string, role: string) => {
    await updateUser.mutateAsync({ userId, data: { role } })
  }

  const handleToggleActive = async (userId: string, isActive: boolean) => {
    if (isActive) {
      await updateUser.mutateAsync({ userId, data: { is_active: true } })
    } else {
      await deactivateUser.mutateAsync(userId)
    }
  }

  const roleBadge = (role: string) => {
    const config: Record<string, { bg: string; text: string; dot: string }> = {
      admin: { bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-400' },
      instructor: { bg: 'bg-violet-500/10', text: 'text-violet-400', dot: 'bg-violet-400' },
      developer: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', dot: 'bg-cyan-400' },
    }
    const c = config[role] || { bg: 'bg-surface-high', text: 'text-text-muted', dot: 'bg-text-muted' }
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-label-sm font-medium ${c.bg} ${c.text}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
        {role}
      </span>
    )
  }

  const initials = (name: string | null, email: string) => {
    if (name) return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    return email.slice(0, 2).toUpperCase()
  }

  const totalPages = Math.ceil((data?.total ?? 0) / 20)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="animate-slide-up">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-violet-500/20">
              <Users className="w-5 h-5 text-primary" />
            </div>
            <h1 className="text-display-lg gradient-text">User Management</h1>
          </div>
          <div className="glass-panel px-4 py-2 flex items-center gap-2">
            <Users className="w-4 h-4 text-primary" />
            <span className="text-label-md text-text-primary font-semibold">{data?.total ?? 0}</span>
            <span className="text-body-sm text-text-muted">total users</span>
          </div>
        </div>
        <p className="text-body-sm text-text-secondary mt-1 ml-11">Manage users, roles, and permissions</p>
      </div>

      {/* Filter Bar */}
      <div className="glass-card p-4 animate-slide-up stagger-1">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input-glow w-full pl-10 pr-4 py-2.5 rounded-lg text-body-sm text-text-primary placeholder:text-text-muted bg-surface-lowest"
            />
          </div>
          <select
            value={roleFilter || ''}
            onChange={e => setRoleFilter(e.target.value || undefined)}
            className="input-glow px-4 py-2.5 rounded-lg text-body-sm text-text-primary bg-surface-lowest appearance-none cursor-pointer"
          >
            <option value="">All Roles</option>
            <option value="developer">Developer</option>
            <option value="instructor">Instructor</option>
            <option value="admin">Admin</option>
          </select>
          <div className="flex items-center gap-1 bg-surface-lowest rounded-lg border border-border-light px-3 py-1">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-3 py-1.5 rounded-md text-label-sm transition-all ${statusFilter === 'all' ? 'bg-primary/20 text-primary' : 'text-text-muted hover:text-text-secondary'}`}
            >
              All
            </button>
            <button
              onClick={() => setStatusFilter('active')}
              className={`px-3 py-1.5 rounded-md text-label-sm transition-all ${statusFilter === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'text-text-muted hover:text-text-secondary'}`}
            >
              Active
            </button>
            <button
              onClick={() => setStatusFilter('inactive')}
              className={`px-3 py-1.5 rounded-md text-label-sm transition-all ${statusFilter === 'inactive' ? 'bg-red-500/20 text-red-400' : 'text-text-muted hover:text-text-secondary'}`}
            >
              Inactive
            </button>
          </div>
        </div>
      </div>

      {/* Users Table */}
      {isLoading ? (
        <div className="glass-card p-12 text-center animate-slide-up stagger-2">
          <div className="inline-flex items-center gap-3 text-text-secondary">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            Loading users...
          </div>
        </div>
      ) : (
        <div className="glass-card overflow-hidden animate-slide-up stagger-2">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-light bg-surface-low/50">
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">User</th>
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">Email</th>
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">Role</th>
                  <th className="px-5 py-3.5 text-center text-label-sm text-text-muted uppercase tracking-wider font-medium">Status</th>
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">Last Login</th>
                  <th className="px-5 py-3.5 text-center text-label-sm text-text-muted uppercase tracking-wider font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.users
                  ?.filter(u => statusFilter === 'all' || (statusFilter === 'active' ? u.is_active : !u.is_active))
                  .map(user => (
                  <tr
                    key={user.id}
                    className="border-b border-border-light/50 hover:bg-surface-low/40 transition-all duration-200 hover:-translate-y-[2px]"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500/30 to-violet-500/30 border border-border-light flex items-center justify-center text-label-sm text-primary font-semibold">
                          {initials(user.full_name, user.email)}
                        </div>
                        <span className="text-text-primary font-medium">{user.full_name || '—'}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-text-secondary text-body-sm">{user.email}</td>
                    <td className="px-5 py-4">
                      <select
                        value={user.role}
                        onChange={e => handleRoleChange(user.id, e.target.value)}
                        className="bg-surface-lowest text-label-sm border border-border-light rounded-lg px-2 py-1 text-text-primary hover:border-primary/40 transition-colors cursor-pointer"
                      >
                        <option value="developer">Developer</option>
                        <option value="instructor">Instructor</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="px-5 py-4 text-center">
                      {user.is_active ? (
                        <span className="inline-flex items-center gap-1.5 badge-success px-2.5 py-0.5 rounded-full text-label-sm">
                          <CheckCircle className="w-3 h-3" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 badge-critical px-2.5 py-0.5 rounded-full text-label-sm">
                          <UserX className="w-3 h-3" /> Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-text-muted text-label-sm font-mono">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-5 py-4 text-center">
                      {user.is_active ? (
                        <button
                          onClick={() => handleToggleActive(user.id, false)}
                          className="btn-ghost text-red-400 hover:!text-red-300 px-3 py-1.5 rounded-lg text-label-sm inline-flex items-center gap-1.5"
                        >
                          <ToggleRight className="w-3.5 h-3.5" /> Deactivate
                        </button>
                      ) : (
                        <button
                          onClick={() => handleToggleActive(user.id, true)}
                          className="btn-ghost text-emerald-400 hover:!text-emerald-300 px-3 py-1.5 rounded-lg text-label-sm inline-flex items-center gap-1.5"
                        >
                          <ToggleLeft className="w-3.5 h-3.5" /> Reactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-5 py-4 border-t border-border-light flex items-center justify-between">
            <span className="text-body-sm text-text-muted">
              Showing <span className="text-text-secondary font-medium">{data?.users?.length ?? 0}</span> of <span className="text-text-secondary font-medium">{data?.total ?? 0}</span> users
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="btn-secondary px-3 py-1.5 rounded-lg text-label-sm flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
              <span className="text-body-sm text-text-muted">
                Page <span className="text-text-primary font-medium">{page}</span> of <span className="text-text-primary font-medium">{totalPages || 1}</span>
              </span>
              <button
                disabled={(data?.users?.length ?? 0) < 20}
                onClick={() => setPage(p => p + 1)}
                className="btn-secondary px-3 py-1.5 rounded-lg text-label-sm flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}