import { useState } from 'react'
import { useAdminUsers, useUpdateUser, useDeactivateUser } from '../hooks/useAdmin'
import { Users, Search, Shield, UserX, CheckCircle } from 'lucide-react'

export function AdminUsersPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string | undefined>(undefined)
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
    const colors: Record<string, string> = {
      admin: 'bg-red-500/20 text-red-400',
      instructor: 'bg-blue-500/20 text-blue-400',
      developer: 'bg-green-500/20 text-green-400',
    }
    return <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[role] || 'bg-surface-3 text-text-muted'}`}>{role}</span>
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Users className="w-6 h-6" /> User Management
          </h1>
          <p className="text-text-secondary mt-1">Manage users, roles, and permissions</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text" placeholder="Search by name or email..." value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-10 w-full"
          />
        </div>
        <select
          value={roleFilter || ''} onChange={e => setRoleFilter(e.target.value || undefined)}
          className="input-field w-auto"
        >
          <option value="">All Roles</option>
          <option value="developer">Developer</option>
          <option value="instructor">Instructor</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {isLoading ? (
        <div className="glass-card p-8 text-center text-text-secondary">Loading users...</div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted text-left">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Last Login</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.users.map(user => (
                  <tr key={user.id} className="border-b border-border/50 hover:bg-surface-2/50">
                    <td className="px-4 py-3 text-text-primary">{user.full_name || '—'}</td>
                    <td className="px-4 py-3 text-text-secondary">{user.email}</td>
                    <td className="px-4 py-3">
                      <select
                        value={user.role}
                        onChange={e => handleRoleChange(user.id, e.target.value)}
                        className="bg-transparent text-xs border border-border rounded px-1 py-0.5"
                      >
                        <option value="developer">Developer</option>
                        <option value="instructor">Instructor</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      {user.is_active
                        ? <span className="flex items-center gap-1 text-green-400"><CheckCircle className="w-3.5 h-3.5" /> Active</span>
                        : <span className="flex items-center gap-1 text-red-400"><UserX className="w-3.5 h-3.5" /> Inactive</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-text-muted text-xs">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-4 py-3">
                      {user.is_active ? (
                        <button onClick={() => handleToggleActive(user.id, false)}
                          className="text-red-400 hover:text-red-300 text-xs">Deactivate</button>
                      ) : (
                        <button onClick={() => handleToggleActive(user.id, true)}
                          className="text-green-400 hover:text-green-300 text-xs">Reactivate</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-border flex items-center justify-between text-sm text-text-muted">
            <span>{data?.total ?? 0} total users</span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="btn-secondary text-xs">Previous</button>
              <button disabled={(data?.users?.length ?? 0) < 20} onClick={() => setPage(p => p + 1)} className="btn-secondary text-xs">Next</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}