import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useUIStore } from '../../store/uiStore'
import {
  Search, Bell, ChevronDown, Settings, LogOut,
  Menu, ChevronRight
} from 'lucide-react'
import type { HeaderProps } from '../../types'

export function Header({ toggleSidebar }: HeaderProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [hasNotifications] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const getBreadcrumbs = () => {
    const pathMap: Record<string, string> = {
      '/': 'Dashboard',
      '/dashboard': 'Dashboard',
      '/projects': 'Projects',
      '/analyses': 'Analyses',
      '/reports': 'Reports',
      '/settings': 'Settings',
    }
    const crumbs = [{ name: 'CodeGuard', path: '/dashboard' }]
    const current = pathMap[location.pathname]
    if (current && current !== 'Dashboard') {
      crumbs.push({ name: current, path: location.pathname })
    }
    return crumbs
  }

  const breadcrumbs = getBreadcrumbs()

  const getInitials = (name: string | null | undefined): string => {
    if (!name) return 'U'
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  return (
    <header className="sticky top-0 z-30 h-16 bg-bg-secondary/80 backdrop-blur-xl border-b border-border-default shrink-0">
      <div className="h-full px-4 md:px-6 flex items-center justify-between gap-4">
        {/* Left: Menu + Breadcrumbs */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <nav className="hidden sm:flex items-center gap-1.5 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <span key={crumb.path} className="flex items-center gap-1.5">
                {index > 0 && <ChevronRight className="w-3.5 h-3.5 text-text-muted" />}
                <button
                  onClick={() => navigate(crumb.path)}
                  className={`transition-colors ${
                    index === breadcrumbs.length - 1
                      ? 'text-text-primary font-medium'
                      : 'text-text-tertiary hover:text-text-secondary'
                  }`}
                >
                  {crumb.name}
                </button>
              </span>
            ))}
          </nav>
        </div>

        {/* Center: Search */}
        <div className="flex-1 max-w-md hidden md:block">
          <button
            onClick={() => useUIStore.getState().openModal('search')}
            className="w-full flex items-center gap-2 pl-3 pr-4 py-2 rounded-lg bg-bg-primary border border-border-default text-sm text-text-muted hover:border-text-muted transition-all duration-200"
          >
            <Search className="w-4 h-4" />
            <span className="flex-1 text-left">Search projects, scans...</span>
            <kbd className="px-1.5 py-0.5 rounded bg-bg-tertiary text-text-muted text-[11px]">Ctrl+K</kbd>
          </button>
        </div>

        {/* Right: Notifications + User Menu */}
        <div className="flex items-center gap-2">
          <button
            className="relative p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50 transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            {hasNotifications && <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-severity-critical ring-2 ring-bg-secondary" />}
          </button>

          <div className="w-px h-6 bg-border-default hidden sm:block" />

          <div ref={userMenuRef} className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2.5 p-1.5 pr-3 rounded-lg hover:bg-bg-tertiary/50 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center text-xs font-bold text-white shrink-0">
                {getInitials(user?.full_name)}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium text-text-primary leading-tight">{user?.full_name || 'User'}</p>
                <p className="text-[11px] text-text-tertiary leading-tight">{user?.email || ''}</p>
              </div>
              <ChevronDown className={`w-4 h-4 text-text-muted transition-transform duration-200 ${isUserMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 top-full mt-2 w-56 rounded-lg glass-card shadow-modal py-1.5 animate-fade-in z-50">
                <div className="sm:hidden px-4 py-3 border-b border-border-default">
                  <p className="text-sm font-medium text-text-primary">{user?.full_name || 'User'}</p>
                  <p className="text-xs text-text-tertiary">{user?.email || ''}</p>
                </div>

                <button
                  onClick={() => { navigate('/settings'); setIsUserMenuOpen(false) }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  <span>Settings</span>
                </button>

                <div className="my-1 border-t border-border-default" />

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-severity-critical/80 hover:text-severity-critical hover:bg-severity-critical-bg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}