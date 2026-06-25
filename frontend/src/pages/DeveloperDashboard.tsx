import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { useDashboardData } from '../hooks/useDashboardData'
import { SkeletonStatCard } from '../components/ui/Skeleton'
import {
  Shield, FolderOpen, FileCode, Bug, CheckCircle, Zap, Plus, AlertTriangle
} from 'lucide-react'

// Dashboard sub-components
import { StatCard } from '../components/dashboard/StatCard'
import { RecentScans } from '../components/dashboard/RecentScans'
import { QuickActions } from '../components/dashboard/QuickActions'
import { SecurityScoreCard } from '../components/dashboard/SecurityScoreCard'
import { VulnerabilitiesCard } from '../components/dashboard/VulnerabilitiesCard'
import { ActivityFeedCard } from '../components/dashboard/ActivityFeedCard'

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function DeveloperDashboard() {
  const { user } = useAuthStore()
  const { addToast } = useUIStore()
  const navigate = useNavigate()
  const { isLoading, error, totalProjects, recentAnalyses, totalCodeFiles, totalVulnerabilities, securityScore } = useDashboardData()
  const [errorShown, setErrorShown] = useState('')

  useEffect(() => {
    const errorMsg = error instanceof Error ? error.message : error ? String(error) : ''
    if (errorMsg && errorMsg !== errorShown) {
      addToast('Failed to load dashboard data', 'error')
      setErrorShown(errorMsg)
    }
  }, [error, errorShown, addToast])

  const stats = [
    {
      title: 'Total Projects',
      value: totalProjects,
      change: '',
      trend: 'up',
      icon: FolderOpen,
      color: 'from-brand-400 to-brand-600',
      glowColor: 'shadow-glow-cyan-sm',
    },
    {
      title: 'Code Files',
      value: totalCodeFiles,
      change: '',
      trend: 'up',
      icon: FileCode,
      color: 'from-accent-400 to-accent-600',
      glowColor: 'shadow-glow-violet',
    },
    {
      title: 'Vulnerabilities',
      value: totalVulnerabilities,
      change: '',
      trend: totalVulnerabilities > 0 ? 'down' : 'up',
      icon: Bug,
      color: 'from-severity-critical to-severity-high',
      glowColor: '',
    },
    {
      title: 'Security Score',
      value: securityScore,
      change: '',
      trend: securityScore >= 70 ? 'up' : 'down',
      icon: Shield,
      color: 'from-success to-brand-500',
      glowColor: 'shadow-glow-cyan-sm',
    },
  ]

  const severityCounts = useMemo(() => {
    const counts = { critical: 0, high: 0, medium: 0, low: 0 }
    recentAnalyses.forEach((analysis: any) => {
      if (analysis.summary && analysis.summary.by_severity) {
        counts.critical += analysis.summary.by_severity.critical || 0
        counts.high += analysis.summary.by_severity.high || 0
        counts.medium += analysis.summary.by_severity.medium || 0
        counts.low += analysis.summary.by_severity.low || 0
      }
    })
    return counts
  }, [recentAnalyses])

  const activityFeed = useMemo(() => {
    const items = recentAnalyses.map((a: any) => {
      const statusConfig: Record<string, { type: string; icon: any; color: string }> = {
        completed: { type: 'scan_completed', icon: CheckCircle, color: 'text-success' },
        running: { type: 'scan_started', icon: Zap, color: 'text-brand-400' },
        failed: { type: 'vulnerability_found', icon: AlertTriangle, color: 'text-severity-high' },
      }
      const config = statusConfig[a.status] || statusConfig.running
      const timeAgo = a.created_at ? formatTimeAgo(new Date(a.created_at)) : 'Unknown'
      const displayName = a.scan_name || a.branch || 'Unknown'
      return { type: config.type, project: displayName, time: timeAgo, icon: config.icon, color: config.color }
    })
    return items.slice(0, 5)
  }, [recentAnalyses])

  const firstName = user?.full_name?.split(' ')[0] || 'User'
  const greetingHour = new Date().getHours()
  const greeting = greetingHour < 12 ? 'Good morning' : greetingHour < 18 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ─── Header ─── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-display-xl font-bold text-on-surface">
            {greeting}, <span className="gradient-text">{firstName}</span>
          </h1>
          <p className="text-body-md text-on-surface-variant mt-1">Here&apos;s what&apos;s happening with your projects today.</p>
        </div>
        <button onClick={() => navigate('/scan')} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg btn-gradient text-body-md font-semibold shrink-0 shadow-glow-cyan-sm">
          <Plus className="w-4 h-4" />
          New Scan
        </button>
      </div>

      {/* ─── Stat Cards ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonStatCard key={i} />)
        ) : stats.map((stat, index) => (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            change={stat.change}
            trend={stat.trend}
            icon={stat.icon}
            color={stat.color}
            glowColor={stat.glowColor}
            index={index}
          />
        ))}
      </div>

      {/* ─── Main Content Grid ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recent Scans + Quick Actions */}
        <div className="lg:col-span-2 space-y-6">
          <RecentScans recentAnalyses={recentAnalyses} isLoading={isLoading} />
          <QuickActions />
        </div>

        {/* Right Sidebar: Security Score + Severity + Activity */}
        <div className="space-y-6">
          <SecurityScoreCard securityScore={securityScore} />
          <VulnerabilitiesCard severityCounts={severityCounts} />
          <ActivityFeedCard activityFeed={activityFeed} />
        </div>
      </div>
    </div>
  )
}
