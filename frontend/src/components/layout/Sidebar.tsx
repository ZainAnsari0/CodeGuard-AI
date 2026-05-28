import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { User, LogOut, Home, Folder, Settings, Shield, FileCode, BarChart, Users, Activity, BookOpen, GraduationCap, UserCheck, Upload } from 'lucide-react'
import type { SidebarProps, Role } from '../../types'

type NavigationItem = {
  name: string
  path: string
  icon: React.ComponentType<{ className?: string }>
}

type RoleBadge = {
  label: string
  color: string
}

const ROLE_NAVIGATION: Record<Role, NavigationItem[]> = {
  developer: [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'New Scan', path: '/scan', icon: Upload },
    { name: 'Projects', path: '/projects', icon: Folder },
    { name: 'Analyses', path: '/analyses', icon: FileCode },
    { name: 'Reports', path: '/reports', icon: BarChart },
    { name: 'Knowledge Base', path: '/knowledge-base', icon: BookOpen },
  ],
  instructor: [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'Classes', path: '/classes', icon: GraduationCap },
    { name: 'Student Progress', path: '/students', icon: UserCheck },
    { name: 'Knowledge Base', path: '/knowledge-base', icon: BookOpen },
  ],
  admin: [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'Users', path: '/users', icon: Users },
    { name: 'System Health', path: '/system-health', icon: Activity },
    { name: 'Event Logs', path: '/event-logs', icon: Shield },
    { name: 'Knowledge Base', path: '/knowledge-base', icon: BookOpen },
  ],
}

const ROLE_BADGES: Record<Role, RoleBadge> = {
  developer: { label: 'Developer', color: 'bg-brand-500/20 text-brand-400' },
  instructor: { label: 'Instructor', color: 'bg-accent-500/20 text-accent-400' },
  admin: { label: 'Admin', color: 'bg-severity-critical/20 text-severity-critical' },
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
    return location.pathname === path
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

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-bg-secondary border-r border-border-default
          transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
          flex flex-col
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Logo section */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-border-default shrink-0">
          <Link to="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-400 to-accent-500 flex items-center justify-center shadow-glow-cyan-sm
              group-hover:shadow-glow-cyan transition-shadow duration-300">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold text-text-primary tracking-tight">
                CodeGuard
              </span>
              <span className="text-[10px] font-medium text-brand-400 tracking-widest uppercase leading-none">
                AI
              </span>
            </div>
          </Link>

          {/* Mobile close button */}
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-1.5 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
            aria-label="Close sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* User profile section */}
        <div className="px-4 py-4 border-b border-border-default shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center text-sm font-bold text-white shrink-0
              shadow-glow-cyan-sm">
              {getInitials(user?.full_name)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{user?.full_name || 'User'}</p>
              <p className="text-xs text-text-tertiary truncate">{user?.email || 'user@example.com'}</p>
              <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${roleBadge.color}`}>
                {roleBadge.label}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <p className="px-3 py-1 text-[11px] font-semibold text-text-muted uppercase tracking-wider">Navigation</p>
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
                    ? 'nav-item-active text-brand-400'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
                  }`}
              >
                <Icon className={`w-5 h-5 shrink-0 transition-colors duration-200
                  ${active ? 'text-brand-400' : 'text-text-muted group-hover:text-brand-400'}`}
                />
                <span>{item.name}</span>
                {active && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400 shadow-glow-cyan-sm" />
                )}
              </Link>
            )
          })}

          <div className="pt-4 pb-2">
            <p className="px-3 py-1 text-[11px] font-semibold text-text-muted uppercase tracking-wider">Settings</p>
          </div>
          <Link
            to="/settings"
            onClick={toggleSidebar}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
              ${location.pathname === '/settings'
                ? 'nav-item-active text-brand-400'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
              }`}
          >
            <Settings className={`w-5 h-5 shrink-0 transition-colors duration-200
              ${location.pathname === '/settings' ? 'text-brand-400' : 'text-text-muted group-hover:text-brand-400'}`}
            />
            <span>Settings</span>
          </Link>
        </nav>

        {/* Logout button */}
        <div className="px-3 py-3 border-t border-border-default shrink-0">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium
              text-severity-critical/80 hover:text-severity-critical hover:bg-severity-critical-bg
              transition-all duration-200 group"
          >
            <LogOut className="w-5 h-5 shrink-0 group-hover:translate-x-0.5 transition-transform" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  )
}