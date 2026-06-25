import { useAuthStore } from '../store/authStore'
import { lazy, Suspense } from 'react'

const DeveloperDashboard = lazy(() => import('./DeveloperDashboard').then(m => ({ default: m.DeveloperDashboard })))
const InstructorDashboard = lazy(() => import('./InstructorDashboard').then(m => ({ default: m.InstructorDashboard })))
const AdminDashboard = lazy(() => import('./AdminDashboard').then(m => ({ default: m.AdminDashboard })))

function DashboardLoader() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center">
      <div className="animate-pulse text-brand-400 text-sm">Loading dashboard...</div>
    </div>
  )
}

export function Dashboard() {
  const { user } = useAuthStore()
  const role = user?.role

  return (
    <Suspense fallback={<DashboardLoader />}>
      {role === 'admin' && <AdminDashboard />}
      {role === 'instructor' && <InstructorDashboard />}
      {(role === 'developer' || !role) && <DeveloperDashboard />}
    </Suspense>
  )
}