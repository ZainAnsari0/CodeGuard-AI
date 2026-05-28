import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { useDashboardData } from '../hooks/useDashboardData'
import { SkeletonStatCard, SkeletonTable } from '../components/ui/Skeleton'
import { SEVERITY_BG_COLORS } from '../utils/severity'
import {
  Shield, FolderOpen, FileCode, Bug, TrendingUp, TrendingDown,
  ArrowRight, Search, Upload, BarChart3, Clock,
  CheckCircle, XCircle, Zap, ChevronRight, Plus, Activity,
  AlertTriangle
} from 'lucide-react'

interface StatItem {
  title: string
  value: number
  change: string
  trend: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  glowColor: string
}

interface RecentScan {
  project: string
  status: string
  critical: number
  high: number
  medium: number
  low: number
  lastScanned: string
}

interface SeverityItem {
  label: string
  count: number
  color: string
  percentage: number
}

interface ActivityItem {
  type: string
  project: string
  time: string
  icon: React.ComponentType<{ className?: string }>
  color: string
}

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

export function Dashboard() {
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

  const stats: StatItem[] = [
    {
      title: 'Total Projects',
      value: totalProjects,
      change: '',
      trend: 'up',
      icon: FolderOpen,
      color: 'from-brand-500 to-brand-600',
      glowColor: 'shadow-glow-cyan-sm',
    },
    {
      title: 'Code Files',
      value: totalCodeFiles,
      change: '',
      trend: 'up',
      icon: FileCode,
      color: 'from-accent-500 to-accent-600',
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

  const recentScans: RecentScan[] = recentAnalyses.map((a: { id: string; status: string; branch: string; created_at: string | null; summary: any }) => ({
    project: a.branch || 'Unknown',
    status: a.status,
    critical: a.summary?.by_severity?.critical || 0,
    high: a.summary?.by_severity?.high || 0,
    medium: a.summary?.by_severity?.medium || 0,
    low: a.summary?.by_severity?.low || 0,
    lastScanned: a.created_at ? new Date(a.created_at).toLocaleDateString() : 'Unknown',
  }))

  // Compute severity counts from actual analysis data
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

  const totalVulns = severityCounts.critical + severityCounts.high + severityCounts.medium + severityCounts.low

  const severityData: SeverityItem[] = [
    { label: 'Critical', count: severityCounts.critical, color: SEVERITY_BG_COLORS.critical, percentage: totalVulns ? Math.round((severityCounts.critical / totalVulns) * 100) : 0 },
    { label: 'High', count: severityCounts.high, color: SEVERITY_BG_COLORS.high, percentage: totalVulns ? Math.round((severityCounts.high / totalVulns) * 100) : 0 },
    { label: 'Medium', count: severityCounts.medium, color: SEVERITY_BG_COLORS.medium, percentage: totalVulns ? Math.round((severityCounts.medium / totalVulns) * 100) : 0 },
    { label: 'Low', count: severityCounts.low, color: SEVERITY_BG_COLORS.low, percentage: totalVulns ? Math.round((severityCounts.low / totalVulns) * 100) : 0 },
  ]

  // Build activity feed from recent analyses
  const activityFeed: ActivityItem[] = useMemo(() => {
    const items: ActivityItem[] = recentAnalyses.map((a: { id: string; status: string; branch: string; created_at: string | null }) => {
      const statusConfig: Record<string, { type: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
        completed: { type: 'scan_completed', icon: CheckCircle, color: 'text-success' },
        running: { type: 'scan_started', icon: Zap, color: 'text-brand-400' },
        failed: { type: 'vulnerability_found', icon: AlertTriangle, color: 'text-severity-high' },
      }
      const config = statusConfig[a.status] || statusConfig.running
      const timeAgo = a.created_at ? formatTimeAgo(new Date(a.created_at)) : 'Unknown'
      return { type: config.type, project: a.branch || 'Unknown', time: timeAgo, icon: config.icon, color: config.color }
    })
    return items.slice(0, 5)
  }, [recentAnalyses])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="badge-low inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium"><CheckCircle className="w-3 h-3" />Completed</span>
      case 'running':
        return <span className="badge-medium inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium"><Activity className="w-3 h-3 animate-pulse" />Running</span>
      case 'failed':
        return <span className="badge-critical inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium"><XCircle className="w-3 h-3" />Failed</span>
      default:
        return <span className="badge-info inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">{status}</span>
    }
  }

  const firstName = user?.full_name?.split(' ')[0] || 'User'
  const greetingHour = new Date().getHours()
  const greeting = greetingHour < 12 ? 'Good morning' : greetingHour < 18 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-text-primary">
            {greeting}, <span className="gradient-text">{firstName}</span>
          </h1>
          <p className="text-text-secondary mt-1">Here&apos;s what&apos;s happening with your projects today.</p>
        </div>
        <button onClick={() => navigate('/scan')} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg btn-gradient text-sm font-medium shrink-0">
          <Plus className="w-4 h-4" />
          New Scan
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonStatCard key={i} />)
        ) : stats.map((stat, index) => {
          const Icon = stat.icon
          const isTrendUp = stat.trend === 'up'
          const isPositiveTrend = stat.title === 'Vulnerabilities' ? !isTrendUp : isTrendUp
          return (
            <div
              key={stat.title}
              className={`glass-card-hover stat-card-glow p-5 stagger-${index + 1}`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center ${stat.glowColor}`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div className={`flex items-center gap-1 text-xs font-medium ${
                  isPositiveTrend ? 'text-success' : 'text-severity-critical'
                }`}>
                  {isTrendUp ? (
                    <TrendingUp className="w-3.5 h-3.5" />
                  ) : (
                    <TrendingDown className="w-3.5 h-3.5" />
                  )}
                  <span>{stat.change}</span>
                </div>
              </div>
              <p className="text-2xl font-bold text-text-primary">{(stat.value ?? 0).toLocaleString()}</p>
              <p className="text-sm text-text-tertiary mt-0.5">{stat.title}</p>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {isLoading ? (
            <SkeletonTable rows={4} cols={5} />
          ) : (
          <div className="glass-card overflow-hidden">
            <div className="px-5 py-4 border-b border-border-default flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-brand-400" />
                <h2 className="text-base font-semibold text-text-primary">Recent Scans</h2>
              </div>
              <button className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1 transition-colors">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border-default">
                    <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Project</th>
                    <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Status</th>
                    <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Severity</th>
                    <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Last Scanned</th>
                    <th className="text-right text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recentScans.map((scan) => (
                    <tr key={scan.project} className="border-b border-border-default/50 hover:bg-bg-card-hover transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-bg-tertiary flex items-center justify-center">
                            <FileCode className="w-4 h-4 text-brand-400" />
                          </div>
                          <span className="text-sm font-medium text-text-primary font-mono">{scan.project}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">{getStatusBadge(scan.status)}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          {scan.critical > 0 && <span className="badge-critical inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{scan.critical}C</span>}
                          {scan.high > 0 && <span className="badge-high inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{scan.high}H</span>}
                          {scan.medium > 0 && <span className="badge-medium inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{scan.medium}M</span>}
                          {scan.low > 0 && <span className="badge-low inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{scan.low}L</span>}
                          {scan.status === 'running' && <span className="text-xs text-text-muted font-mono">--</span>}
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-sm text-text-tertiary">{scan.lastScanned}</span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button className="text-text-muted hover:text-brand-400 transition-colors p-1">
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="md:hidden divide-y divide-border-default/50">
              {recentScans.map((scan) => (
                <div key={scan.project} className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-bg-tertiary flex items-center justify-center">
                        <FileCode className="w-4 h-4 text-brand-400" />
                      </div>
                      <span className="text-sm font-medium text-text-primary font-mono">{scan.project}</span>
                    </div>
                    {getStatusBadge(scan.status)}
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      {scan.critical > 0 && <span className="badge-critical px-1.5 py-0.5 rounded text-[11px] font-mono">{scan.critical}C</span>}
                      {scan.high > 0 && <span className="badge-high px-1.5 py-0.5 rounded text-[11px] font-mono">{scan.high}H</span>}
                      {scan.medium > 0 && <span className="badge-medium px-1.5 py-0.5 rounded text-[11px] font-mono">{scan.medium}M</span>}
                      {scan.low > 0 && <span className="badge-low px-1.5 py-0.5 rounded text-[11px] font-mono">{scan.low}L</span>}
                    </div>
                    <span className="text-xs text-text-muted">{scan.lastScanned}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: 'New Scan', description: 'Analyze a new codebase', icon: Search, gradient: 'from-brand-500 to-brand-600', path: '/scan' },
              { label: 'Upload Code', description: 'Upload files for scanning', icon: Upload, gradient: 'from-accent-500 to-accent-600', path: '/scan' },
              { label: 'View Reports', description: 'Browse detailed reports', icon: BarChart3, gradient: 'from-brand-400 to-accent-500', path: '/history' },
            ].map((action) => {
              const Icon = action.icon
              return (
                <button
                  key={action.label}
                  onClick={() => navigate(action.path)}
                  className="glass-card-hover p-4 text-left group transition-all duration-200"
                >
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${action.gradient} flex items-center justify-center mb-3
                    group-hover:shadow-glow-cyan transition-shadow duration-300`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <p className="text-sm font-medium text-text-primary group-hover:text-brand-400 transition-colors">{action.label}</p>
                  <p className="text-xs text-text-muted mt-0.5">{action.description}</p>
                </button>
              )
            })}
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <Bug className="w-4 h-4 text-severity-critical" />
                <h2 className="text-base font-semibold text-text-primary">Vulnerabilities</h2>
              </div>
              <span className="text-xs text-text-muted font-mono">{totalVulns} total</span>
            </div>

            <div className="space-y-4">
              {severityData.map((item) => (
                <div key={item.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                      <span className="text-sm text-text-secondary">{item.label}</span>
                    </div>
                    <span className="text-sm font-medium text-text-primary font-mono">{item.count}</span>
                  </div>
                  <div className="severity-bar">
                    <div
                      className={`severity-bar-fill ${item.color}`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-5 pt-4 border-t border-border-default">
              <div className="flex items-center justify-between">
                <div className="text-center">
                  <p className="text-2xl font-bold text-severity-critical font-mono">{severityCounts.critical}</p>
                  <p className="text-[11px] text-text-muted uppercase tracking-wider">Critical</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-severity-high font-mono">{severityCounts.high}</p>
                  <p className="text-[11px] text-text-muted uppercase tracking-wider">High</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-severity-medium font-mono">{severityCounts.medium}</p>
                  <p className="text-[11px] text-text-muted uppercase tracking-wider">Medium</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-brand-400 font-mono">{severityCounts.low}</p>
                  <p className="text-[11px] text-text-muted uppercase tracking-wider">Low</p>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-brand-400" />
                <h2 className="text-base font-semibold text-text-primary">Activity</h2>
              </div>
            </div>

            <div className="space-y-3">
              {activityFeed.map((activity, index) => {
                const Icon = activity.icon
                return (
                  <div key={index} className="flex items-start gap-3 group">
                    <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center shrink-0
                      ${activity.color === 'text-success' ? 'bg-success/10' :
                        activity.color === 'text-severity-high' ? 'bg-severity-high/10' :
                        activity.color === 'text-brand-400' ? 'bg-brand-500/10' :
                        'bg-accent-500/10'}`}>
                      <Icon className={`w-3.5 h-3.5 ${activity.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-primary leading-snug">
                        {activity.type === 'scan_completed' && 'Scan completed'}
                        {activity.type === 'vulnerability_found' && 'New vulnerabilities found'}
                        {activity.type === 'scan_started' && 'Scan started'}
                        {activity.type === 'project_added' && 'Project added'}
                      </p>
                      <p className="text-xs text-text-muted mt-0.5 truncate">{activity.project}</p>
                    </div>
                    <span className="text-[11px] text-text-muted whitespace-nowrap flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {activity.time}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}