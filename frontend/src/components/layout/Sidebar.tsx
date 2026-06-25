import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { User, LogOut, Home, Folder, Settings, Shield, FileCode, BarChart, Users, Activity, BookOpen, GraduationCap, UserCheck, Upload, History, Plus, ChevronLeft } from 'lucide-react'
import type { SidebarProps, Role } from '../../types'

type NavigationItem = {
  name: string
  path: string
  icon: React.ComponentType<{ className?: string }>
  description?: string
}

type RoleBadge = {
  label: string
  color: string
}

const ROLE_NAVIGATION: Record<Role, NavigationItem[]> = {
  developer: [
    { name: 'Dashboard', path: '/dashboard', icon: Home, description: 'Overview' },
    { name: 'New Scan', path: '/scan', icon: Upload, description: 'Upload code' },
    { name: 'My Classes', path: '/my-classes', icon: GraduationCap, description: 'Joined classes' },
    { name: 'Scan History', path: '/history', icon: History, description: 'Past scans' },
    { name: 'Knowledge Base', path: '/knowledge-base', icon: BookOpen, description: 'Learn more' },
  ],
  instructor: [
    { name: 'Dashboard', path: '/dashboard', icon: Home, description: 'Overview' },
    { name: 'Classes', path: '/classes', icon: GraduationCap, description: 'Manage classes' },
    { name: 'Student Progress', path: '/students', icon: UserCheck, description: 'Track progress' },
    { name: 'Knowledge Base', path: '/knowledge-base', icon: BookOpen, description: 'Learn more' },
  ],
  admin: [
    { name: 'Dashboard', path: '/dashboard', icon: Home, description: 'Overview' },
    { name: 'User Management', path: '/users', icon: Users, description: 'Manage users' },
    { name: 'System Health', path: '/system-health', icon: Activity, description: 'Monitor system' },
    { name: 'Event Logs', path: '/event-logs', icon: Shield, description: 'Audit trail' },
    { name: 'Knowledge Base', path: '/knowledge-base', icon: BookOpen, description: 'Learn more' },
  ],
}

const ROLE_BADGES: Record<Role, RoleBadge> = {
  developer: { label: 'Developer', color: 'bg-brand-500/20 text-brand-400 border border-brand-500/30' },
  instructor: { label: 'Instructor', color: 'bg-accent-500/20 text-accent-400 border border-accent-500/30' },
  admin: { label: 'Admin', color: 'bg-severity-critical/15 text-severity-critical border border-severity-critical/25' },
}

export function Sidebar({ isOpen, toggleSidebar }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const role: Role = (user?.role as Role) || 'developer'

  const navigation = ROLE_NAVIGATION[role] || ROLE_NAVIGATION.developer
  const roleBadge = ROLE_BADGES[role] || ROLE_BADGES.developer

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const getInitials = (name: string | null | undefined): string => {
    if (!name) return 'U'
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  const isActive = (path: string): boolean => {
    if (path === '/dashboard') {
      return location.pathname === '/' || location.pathname === '/dashboard'
    }
    return location.pathname.startsWith(path)
  }

  return (
    <>
      {/* Mobile backdrop overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden animate-fade-in"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar — 256px matching Stitch design */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-[256px] bg-surface-container border-r border-outline-variant/50
          transform transition-transform duration-300 ease-in-out lg:translate-x-0
          flex flex-col
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* ─── Brand Header ─── */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-outline-variant/50 shrink-0">
          <Link to="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan-sm
              group-hover:shadow-glow-cyan transition-shadow duration-300">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold text-on-surface tracking-tight">
                CodeGuard
              </span>
              <span className="text-label-sm text-brand-400 tracking-widest uppercase leading-none">
                AI
              </span>
            </div>
          </Link>

          {/* Mobile close button */}
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-high transition-colors"
            aria-label="Close sidebar"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>

        {/* ─── New Scan CTA ─── */}
        {role === 'developer' && (
          <div className="px-4 pt-5 pb-2 animate-fade-in">
            <button
              onClick={() => navigate('/scan')}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg btn-gradient text-sm font-semibold"
            >
              <Plus className="w-4 h-4" />
              New Scan
            </button>
          </div>
        )}


        {/* ─── User Profile Section ─── */}
        <div className="px-4 py-4 border-b border-outline-variant/50 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center text-sm font-bold text-white shrink-0 shadow-glow-cyan-sm">
              {getInitials(user?.full_name)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-on-surface truncate">{user?.full_name || 'User'}</p>
              <p className="text-xs text-on-surface-variant truncate">{user?.email || 'user@example.com'}</p>
              <span className={`inline-block mt-1.5 px-2 py-0.5 rounded text-label-sm uppercase tracking-wider ${roleBadge.color}`}>
                {roleBadge.label}
              </span>
            </div>
          </div>
        </div>

        {/* ─── Navigation ─── */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <p className="px-3 py-1 text-label-sm font-medium text-on-surface-variant/60 uppercase tracking-wider">Navigation</p>
          {navigation.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={toggleSidebar}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
                  ${active
                    ? 'nav-item-active text-primary'
                    : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-high/50'
                  }`}
              >
                <Icon className={`w-5 h-5 shrink-0 transition-colors duration-200
                  ${active ? 'text-primary' : 'text-on-surface-variant/60 group-hover:text-primary'}`}
                />
                <span>{item.name}</span>
                {active && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-glow-cyan-sm" />
                )}
              </Link>
            )
          })}

          <div className="pt-4 pb-2">
            <p className="px-3 py-1 text-label-sm font-medium text-on-surface-variant/60 uppercase tracking-wider">Settings</p>
          </div>
          <Link
            to="/settings"
            onClick={toggleSidebar}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
              ${location.pathname === '/settings'
                ? 'nav-item-active text-primary'
                : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-high/50'
              }`}
          >
            <Settings className={`w-5 h-5 shrink-0 transition-colors duration-200
              ${location.pathname === '/settings' ? 'text-primary' : 'text-on-surface-variant/60 group-hover:text-primary'}`}
            />
            <span>Settings</span>
          </Link>
        </nav>

        {/* ─── Footer ─── */}
        <div className="px-4 py-3 border-t border-outline-variant/50 shrink-0">
          <div className="flex items-center justify-between mb-2">
            <a href="#" className="text-xs text-on-surface-variant/60 hover:text-on-surface-variant transition-colors">Docs</a>
            <a href="#" className="text-xs text-on-surface-variant/60 hover:text-on-surface-variant transition-colors">Support</a>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium
              text-severity-critical/70 hover:text-severity-critical hover:bg-severity-critical-bg
              transition-all duration-200 group"
          >
            <LogOut className="w-4 h-5 shrink-0 group-hover:translate-x-0.5 transition-transform" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  )
}