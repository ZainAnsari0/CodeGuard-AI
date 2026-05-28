import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useState, useEffect, Suspense, lazy } from 'react'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { Footer } from './components/layout/Footer'
import { ErrorPage, OfflinePage } from './pages/ErrorPage'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { ToastContainer } from './components/ui/ToastContainer'
import { SearchModal } from './components/ui/SearchModal'
import { OnboardingTour } from './components/ui/OnboardingTour'
import { useAuthStore } from './store/authStore'
import { useUIStore } from './store/uiStore'
import './index.css'

// Lazy-loaded pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })))
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })))
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword').then(m => ({ default: m.ForgotPassword })))
const ResetPassword = lazy(() => import('./pages/ResetPassword').then(m => ({ default: m.ResetPassword })))
const ScanPage = lazy(() => import('./pages/ScanPage').then(m => ({ default: m.ScanPage })))
const ScanProgress = lazy(() => import('./pages/ScanProgress').then(m => ({ default: m.ScanProgress })))
const ReportPage = lazy(() => import('./pages/ReportPage').then(m => ({ default: m.ReportPage })))
const ScanHistoryPage = lazy(() => import('./pages/ScanHistoryPage').then(m => ({ default: m.ScanHistoryPage })))
const ClassesPage = lazy(() => import('./pages/ClassesPage').then(m => ({ default: m.ClassesPage })))
const ClassMetricsPage = lazy(() => import('./pages/ClassMetricsPage').then(m => ({ default: m.ClassMetricsPage })))
const AdminUsersPage = lazy(() => import('./pages/AdminUsersPage').then(m => ({ default: m.AdminUsersPage })))
const SystemHealthPage = lazy(() => import('./pages/SystemHealthPage').then(m => ({ default: m.SystemHealthPage })))
const EventLogsPage = lazy(() => import('./pages/EventLogsPage').then(m => ({ default: m.EventLogsPage })))
const KnowledgeBasePage = lazy(() => import('./pages/KnowledgeBasePage').then(m => ({ default: m.KnowledgeBasePage })))
const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })))
const GuestDemoPage = lazy(() => import('./pages/GuestDemoPage').then(m => ({ default: m.GuestDemoPage })))
const SharedReportPage = lazy(() => import('./pages/SharedReportPage').then(m => ({ default: m.SharedReportPage })))
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })))

function PageLoader() {
  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center">
      <div className="animate-pulse text-brand-400 text-sm">Loading...</div>
    </div>
  )
}

function App() {
  const location = useLocation()
  const { isAuthenticated } = useAuthStore()
  const { sidebarOpen, setSidebarOpen, toggleSidebar, openModal } = useUIStore()

  const authPaths = ['/login', '/register', '/forgot-password', '/reset-password']
  const isAuthPage = authPaths.includes(location.pathname)

  // Public pages that don't need sidebar/header layout
  const publicPaths = ['/demo', '/share', '/landing']
  const isPublicPage = publicPaths.some(p => location.pathname.startsWith(p))

  // Offline detection
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const handleOffline = () => setIsOffline(true)
    const handleOnline = () => setIsOffline(false)
    window.addEventListener('offline', handleOffline)
    window.addEventListener('online', handleOnline)
    return () => {
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('online', handleOnline)
    }
  }, [])

  // Cmd/Ctrl+K to open search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        openModal('search')
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [openModal])

  // Show offline page
  if (isOffline && !isAuthPage && !isPublicPage) {
    return (
      <ErrorBoundary>
        <OfflinePage />
      </ErrorBoundary>
    )
  }

  if (isAuthPage) {
    return (
      <ErrorBoundary>
        <Suspense fallback={<PageLoader />}>
          <div className="min-h-screen bg-bg-primary">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
            </Routes>
          </div>
        </Suspense>
      </ErrorBoundary>
    )
  }

  // Public pages with minimal layout (accessible to all users)
  if (isPublicPage) {
    return (
      <ErrorBoundary>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/demo" element={<GuestDemoPage />} />
            <Route path="/share/:token" element={<SharedReportPage />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    )
  }

  // Landing page for unauthenticated users at /
  if (location.pathname === '/' && !isAuthenticated) {
    return (
      <ErrorBoundary>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-bg-primary flex">
        <Sidebar isOpen={sidebarOpen} toggleSidebar={() => setSidebarOpen(false)} />

        <div className="flex-1 flex flex-col min-h-screen lg:ml-64">
          <Header toggleSidebar={toggleSidebar} />

          <main className="flex-1 p-4 md:p-6 lg:p-8">
            <OnboardingTour />
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/knowledge-base" element={<ProtectedRoute><KnowledgeBasePage /></ProtectedRoute>} />
                <Route path="/knowledge-base/:slug" element={<ProtectedRoute><KnowledgeBasePage /></ProtectedRoute>} />
                <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
                <Route path="/scan" element={<ProtectedRoute><ScanPage /></ProtectedRoute>} />
                <Route path="/scan/:scanId/progress" element={<ProtectedRoute><ScanProgress /></ProtectedRoute>} />
                <Route path="/scan/:scanId/report" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
                <Route path="/history" element={<ProtectedRoute><ScanHistoryPage /></ProtectedRoute>} />

                {/* Instructor routes */}
                <Route path="/classes" element={<ProtectedRoute allowedRoles={['instructor', 'admin']}><ClassesPage /></ProtectedRoute>} />
                <Route path="/classes/:classId/metrics" element={<ProtectedRoute allowedRoles={['instructor', 'admin']}><ClassMetricsPage /></ProtectedRoute>} />
                <Route path="/students" element={<ProtectedRoute allowedRoles={['instructor', 'admin']}><ClassesPage /></ProtectedRoute>} />

                {/* Admin routes */}
                <Route path="/users" element={<ProtectedRoute allowedRoles={['admin']}><AdminUsersPage /></ProtectedRoute>} />
                <Route path="/system-health" element={<ProtectedRoute allowedRoles={['admin']}><SystemHealthPage /></ProtectedRoute>} />
                <Route path="/event-logs" element={<ProtectedRoute allowedRoles={['admin']}><EventLogsPage /></ProtectedRoute>} />

                {/* Error pages */}
                <Route path="/403" element={<ErrorPage code={403} />} />
                <Route path="/500" element={<ErrorPage code={500} />} />
                <Route path="*" element={<ErrorPage code={404} />} />
              </Routes>
            </Suspense>
          </main>

          <Footer />
        </div>
      </div>

      <ToastContainer />
      <SearchModal />
    </ErrorBoundary>
  )
}

export default App