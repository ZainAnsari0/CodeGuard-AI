import { useSystemHealth, useEventLogs } from '../hooks/useAdmin'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import { Shield, Users, Activity, Settings, ArrowRight, Server, FileText, CheckCircle2, AlertOctagon } from 'lucide-react'
import { StatCard } from '../components/dashboard/StatCard'
import { SkeletonStatCard } from '../components/ui/Skeleton'

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / (3600 * 24))
  const h = Math.floor((seconds % (3600 * 24)) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}d ${h}h`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

export function AdminDashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { data: health, isLoading: isHealthLoading } = useSystemHealth()
  const { data: logs, isLoading: isLogsLoading } = useEventLogs(1, 5)

  const firstName = user?.full_name?.split(' ')[0] || 'Admin'
  const greetingHour = new Date().getHours()
  const greeting = greetingHour < 12 ? 'Good morning' : greetingHour < 18 ? 'Good afternoon' : 'Good evening'

  const totalUsers = health?.stats?.total_users ?? 0
  const totalScans = health?.stats?.total_scans ?? 0
  const uptime = health?.uptime_seconds ? formatUptime(health.uptime_seconds) : 'Unknown'
  const overallStatus = health?.status || 'Unknown'

  const stats = [
    {
      title: 'Total Users',
      value: totalUsers,
      icon: Users,
      color: 'from-brand-400 to-brand-600',
      glowColor: 'shadow-glow-cyan-sm',
    },
    {
      title: 'Total Scans Run',
      value: totalScans,
      icon: Activity,
      color: 'from-accent-400 to-accent-600',
      glowColor: 'shadow-glow-violet',
    },
    {
      title: 'System Uptime',
      value: uptime,
      icon: Server,
      color: 'from-success to-brand-500',
      glowColor: 'shadow-glow-cyan-sm',
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ─── Header ─── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-display-xl font-bold text-on-surface flex items-center gap-3">
            {greeting}, <span className="gradient-text">{firstName}</span>
            <span className="text-xs bg-severity-critical/15 text-severity-critical border border-severity-critical/20 px-2 py-0.5 rounded uppercase font-bold tracking-widest leading-none">
              Superuser
            </span>
          </h1>
          <p className="text-body-md text-on-surface-variant mt-1">Platform administration control center.</p>
        </div>
        <button
          onClick={() => navigate('/system-health')}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg btn-gradient text-body-md font-semibold shrink-0 shadow-glow-cyan-sm"
        >
          <Settings className="w-4 h-4" />
          System Health
        </button>
      </div>

      {/* ─── Stats Grid ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {isHealthLoading ? (
          Array.from({ length: 3 }).map((_, i) => <SkeletonStatCard key={i} />)
        ) : (
          stats.map((stat, index) => (
            <StatCard
              key={stat.title}
              title={stat.title}
              value={stat.value}
              change=""
              trend="up"
              icon={stat.icon}
              color={stat.color}
              glowColor={stat.glowColor}
              index={index}
            />
          ))
        )}
      </div>

      {/* ─── Main Content Grid ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left/Middle Column: Services Status & Recent Events */}
        <div className="lg:col-span-2 space-y-6">
          {/* Services Health */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-headline-sm font-bold text-on-surface border-b border-outline-variant/30 pb-3 flex items-center gap-2">
              <Server className="w-5 h-5 text-brand-400" />
              Infrastructure Subsystems
            </h2>

            {isHealthLoading ? (
              <p className="text-center py-6 text-on-surface-variant">Loading service state...</p>
            ) : !health?.services?.length ? (
              <p className="text-center py-6 text-on-surface-variant">No services reported.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {health.services.map((svc) => (
                  <div
                    key={svc.name}
                    className="p-3.5 rounded-xl bg-surface-high/40 border border-outline-variant/20 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${svc.status === 'healthy' ? 'bg-success/10 text-success' : 'bg-severity-critical/10 text-severity-critical'}`}>
                        {svc.status === 'healthy' ? <CheckCircle2 className="w-4 h-4" /> : <AlertOctagon className="w-4 h-4" />}
                      </div>
                      <div>
                        <p className="text-body-md font-bold text-on-surface capitalize">{svc.name}</p>
                        {svc.latency_ms !== null && (
                          <p className="text-label-sm text-on-surface-variant">{svc.latency_ms}ms response time</p>
                        )}
                      </div>
                    </div>
                    <span className={`text-label-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${svc.status === 'healthy' ? 'bg-success/15 text-success' : 'bg-severity-critical/15 text-severity-critical'}`}>
                      {svc.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Events/Logs */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
              <h2 className="text-headline-sm font-bold text-on-surface flex items-center gap-2">
                <FileText className="w-5 h-5 text-accent-400" />
                Audit Trail
              </h2>
              <button
                onClick={() => navigate('/event-logs')}
                className="text-label-md text-brand-400 hover:text-brand-300 font-semibold transition-colors flex items-center gap-1"
              >
                View All <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {isLogsLoading ? (
              <p className="text-center py-6 text-on-surface-variant">Loading audit logs...</p>
            ) : !logs?.events?.length ? (
              <p className="text-center py-6 text-on-surface-variant">No system events logged.</p>
            ) : (
              <div className="space-y-2.5">
                {logs.events.map((evt) => (
                  <div
                    key={evt.id}
                    className="p-3 rounded-lg bg-surface-high/20 border border-outline-variant/10 text-body-sm flex justify-between gap-4"
                  >
                    <div className="space-y-0.5">
                      <p className="text-on-surface font-semibold">{evt.message}</p>
                      <p className="text-label-sm text-on-surface-variant">{evt.event_type} • {evt.created_at ? new Date(evt.created_at).toLocaleString() : 'Unknown'}</p>
                    </div>
                    <span className={`text-label-xs font-mono h-fit px-1.5 py-0.5 rounded uppercase ${
                      evt.severity === 'error' || evt.severity === 'critical'
                        ? 'bg-severity-critical/15 text-severity-critical'
                        : evt.severity === 'warning'
                        ? 'bg-severity-medium/15 text-severity-medium'
                        : 'bg-brand-500/10 text-brand-400'
                    }`}>
                      {evt.severity}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Quick Actions & Settings */}
        <div className="space-y-4">
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-headline-sm font-bold text-on-surface border-b border-outline-variant/30 pb-3 flex items-center gap-2">
              <Shield className="w-5 h-5 text-brand-400" />
              Administrative Tools
            </h2>
            <div className="space-y-2">
              <button
                onClick={() => navigate('/users')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-surface-high/40 hover:bg-surface-high/80 border border-outline-variant/20 hover:border-brand-400/40 text-left transition-all"
              >
                <div>
                  <p className="text-body-md font-semibold text-on-surface">User Management</p>
                  <p className="text-label-sm text-on-surface-variant">Modify roles, unlock accounts</p>
                </div>
                <ArrowRight className="w-5 h-5 text-on-surface-variant" />
              </button>

              <button
                onClick={() => navigate('/system-health')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-surface-high/40 hover:bg-surface-high/80 border border-outline-variant/20 hover:border-brand-400/40 text-left transition-all"
              >
                <div>
                  <p className="text-body-md font-semibold text-on-surface">System Monitoring</p>
                  <p className="text-label-sm text-on-surface-variant">Performance metrics and token count</p>
                </div>
                <ArrowRight className="w-5 h-5 text-on-surface-variant" />
              </button>

              <button
                onClick={() => navigate('/event-logs')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-surface-high/40 hover:bg-surface-high/80 border border-outline-variant/20 hover:border-brand-400/40 text-left transition-all"
              >
                <div>
                  <p className="text-body-md font-semibold text-on-surface">Audit Logs</p>
                  <p className="text-label-sm text-on-surface-variant">Security and authentication events</p>
                </div>
                <ArrowRight className="w-5 h-5 text-on-surface-variant" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
