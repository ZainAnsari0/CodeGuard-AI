import { useSystemHealth, useTokenUsage } from '../hooks/useAdmin'
import { Activity, CheckCircle, AlertTriangle, XCircle, Cpu, Users, ScanLine, Clock, Tag } from 'lucide-react'

export function SystemHealthPage() {
  const { data: health, isLoading } = useSystemHealth()
  const { data: tokenData } = useTokenUsage()

  const statusDot = (status: string) => {
    switch (status) {
      case 'healthy':
        return (
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
          </span>
        )
      case 'degraded':
        return (
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-400" />
          </span>
        )
      case 'unavailable':
        return <span className="inline-flex rounded-full h-2.5 w-2.5 bg-red-400" />
      default:
        return <span className="inline-flex rounded-full h-2.5 w-2.5 bg-slate-500" />
    }
  }

  const statusLabel = (status: string) => {
    const map: Record<string, { text: string; cls: string }> = {
      healthy: { text: 'Healthy', cls: 'text-emerald-400' },
      degraded: { text: 'Degraded', cls: 'text-amber-400' },
      unavailable: { text: 'Down', cls: 'text-red-400' },
    }
    const entry = map[status] || { text: status, cls: 'text-text-muted' }
    return <span className={`text-label-sm ${entry.cls}`}>{entry.text}</span>
  }

  const stats = [
    { label: 'Total Users', value: health?.stats?.total_users?.toLocaleString() ?? '—', icon: Users, color: 'from-cyan-500/20 to-cyan-500/5' },
    { label: 'Total Scans', value: health?.stats?.total_scans?.toLocaleString() ?? '—', icon: ScanLine, color: 'from-violet-500/20 to-violet-500/5' },
    { label: 'Uptime', value: health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : '—', icon: Clock, color: 'from-emerald-500/20 to-emerald-500/5' },
    { label: 'Version', value: health?.version ?? '—', icon: Tag, color: 'from-amber-500/20 to-amber-500/5' },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="animate-slide-up">
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 rounded-lg bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/20">
            <Activity className="w-5 h-5 text-primary" />
          </div>
          <h1 className="text-display-lg gradient-text">System Health</h1>
        </div>
        <p className="text-body-sm text-text-secondary ml-11">Monitor infrastructure and service status</p>
      </div>

      {isLoading ? (
        <div className="glass-card p-12 text-center animate-slide-up stagger-1">
          <div className="inline-flex items-center gap-3 text-text-secondary">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            Loading system status...
          </div>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat, i) => (
              <div
                key={stat.label}
                className={`glass-card-hover stat-card-glow p-5 animate-slide-up stagger-${i + 1}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-label-sm text-text-muted uppercase tracking-wider">{stat.label}</span>
                  <div className={`p-1.5 rounded-md bg-gradient-to-br ${stat.color}`}>
                    <stat.icon className="w-4 h-4 text-primary" />
                  </div>
                </div>
                <p className="text-display-xl text-text-primary">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* Overall Status + Services */}
          <div className="glass-card p-6 animate-slide-up stagger-3">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-headline-sm text-text-primary flex items-center gap-2">
                Core Services
              </h3>
              <span className={`px-3 py-1 rounded-full text-label-sm font-medium ${
                health?.status === 'healthy'
                  ? 'badge-success'
                  : health?.status === 'degraded'
                    ? 'badge-medium'
                    : 'badge-critical'
              }`}>
                {health?.status === 'healthy' ? 'All Systems Operational' : health?.status === 'degraded' ? 'Partial Degradation' : 'System Issues'}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {health?.services?.map(svc => (
                <div
                  key={svc.name}
                  className="flex items-center justify-between p-4 rounded-lg bg-surface-low border border-border-light hover:border-primary/30 transition-all duration-200"
                >
                  <div className="flex items-center gap-3">
                    {statusDot(svc.status)}
                    <span className="text-body-md text-text-primary font-medium">{svc.name}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    {svc.latency_ms != null && (
                      <span className="text-label-sm text-text-muted font-mono">{svc.latency_ms}ms</span>
                    )}
                    {statusLabel(svc.status)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Provider Usage */}
          {tokenData?.token_usage && (
            <div className="glass-card p-6 animate-slide-up stagger-4">
              <h3 className="text-headline-sm text-text-primary mb-5 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-primary" />
                AI Provider Usage
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-light">
                      <th className="px-4 py-3 text-left text-label-sm text-text-muted uppercase tracking-wider">Provider</th>
                      <th className="px-4 py-3 text-right text-label-sm text-text-muted uppercase tracking-wider">Calls</th>
                      <th className="px-4 py-3 text-right text-label-sm text-text-muted uppercase tracking-wider">Input Tokens</th>
                      <th className="px-4 py-3 text-right text-label-sm text-text-muted uppercase tracking-wider">Output Tokens</th>
                      <th className="px-4 py-3 text-right text-label-sm text-text-muted uppercase tracking-wider">Est. Cost</th>
                      <th className="px-4 py-3 text-center text-label-sm text-text-muted uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(tokenData.token_usage.by_provider).map(([provider, usage]) => (
                      <tr key={provider} className="border-b border-border-light/50 hover:bg-surface-low/50 transition-colors">
                        <td className="px-4 py-3 text-text-primary font-medium">{provider}</td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-right">{usage.total_calls.toLocaleString()}</td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-right">{usage.total_input_tokens.toLocaleString()}</td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-right">{usage.total_output_tokens.toLocaleString()}</td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-right">${usage.total_cost.toFixed(4)}</td>
                        <td className="px-4 py-3 text-center">
                          {tokenData.provider_status[provider] ? (
                            <span className="inline-flex items-center gap-1.5 badge-success px-2.5 py-0.5 rounded-full text-label-sm">
                              <CheckCircle className="w-3 h-3" /> Available
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 badge-critical px-2.5 py-0.5 rounded-full text-label-sm">
                              <XCircle className="w-3 h-3" /> Down
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}