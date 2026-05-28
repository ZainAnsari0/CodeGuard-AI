import { useSystemHealth, useTokenUsage } from '../hooks/useAdmin'
import { Activity, CheckCircle, AlertTriangle, XCircle, Cpu, DollarSign } from 'lucide-react'

export function SystemHealthPage() {
  const { data: health, isLoading } = useSystemHealth()
  const { data: tokenData } = useTokenUsage()

  const statusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-green-400" />
      case 'degraded': return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      case 'unavailable': return <XCircle className="w-5 h-5 text-text-muted" />
      default: return <Activity className="w-5 h-5 text-text-muted" />
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Activity className="w-6 h-6" /> System Health
        </h1>
        <p className="text-text-secondary mt-1">Monitor infrastructure and service status</p>
      </div>

      {isLoading ? (
        <div className="glass-card p-8 text-center text-text-secondary">Loading...</div>
      ) : (
        <>
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Overall Status</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                health?.status === 'healthy' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
              }`}>{health?.status || 'unknown'}</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-surface-2 rounded-lg p-3 text-center">
                <p className="text-text-muted text-xs">Users</p>
                <p className="text-xl font-bold text-text-primary">{health?.stats?.total_users ?? '—'}</p>
              </div>
              <div className="bg-surface-2 rounded-lg p-3 text-center">
                <p className="text-text-muted text-xs">Scans</p>
                <p className="text-xl font-bold text-text-primary">{health?.stats?.total_scans ?? '—'}</p>
              </div>
              <div className="bg-surface-2 rounded-lg p-3 text-center">
                <p className="text-text-muted text-xs">Uptime</p>
                <p className="text-xl font-bold text-text-primary">{health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 3600)}h` : '—'}</p>
              </div>
              <div className="bg-surface-2 rounded-lg p-3 text-center">
                <p className="text-text-muted text-xs">Version</p>
                <p className="text-xl font-bold text-text-primary">{health?.version ?? '—'}</p>
              </div>
            </div>

            <h4 className="font-medium text-text-primary mb-3">Services</h4>
            <div className="space-y-2">
              {health?.services?.map(svc => (
                <div key={svc.name} className="flex items-center justify-between p-3 rounded bg-surface-2">
                  <div className="flex items-center gap-3">
                    {statusIcon(svc.status)}
                    <span className="text-text-primary font-medium">{svc.name}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    {svc.latency_ms != null && <span className="text-text-muted text-xs">{svc.latency_ms}ms</span>}
                    <span className={`text-xs font-medium ${
                      svc.status === 'healthy' ? 'text-green-400' : svc.status === 'degraded' ? 'text-yellow-400' : 'text-text-muted'
                    }`}>{svc.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {tokenData?.token_usage && (
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                <Cpu className="w-5 h-5" /> Token Usage
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-text-muted text-left">
                      <th className="px-3 py-2">Provider</th>
                      <th className="px-3 py-2">Calls</th>
                      <th className="px-3 py-2">Input Tokens</th>
                      <th className="px-3 py-2">Output Tokens</th>
                      <th className="px-3 py-2">Est. Cost</th>
                      <th className="px-3 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(tokenData.token_usage.by_provider).map(([provider, usage]) => (
                      <tr key={provider} className="border-b border-border/50">
                        <td className="px-3 py-2 text-text-primary">{provider}</td>
                        <td className="px-3 py-2 text-text-secondary font-mono">{usage.total_calls}</td>
                        <td className="px-3 py-2 text-text-secondary font-mono">{usage.total_input_tokens.toLocaleString()}</td>
                        <td className="px-3 py-2 text-text-secondary font-mono">{usage.total_output_tokens.toLocaleString()}</td>
                        <td className="px-3 py-2 text-text-secondary font-mono">${usage.total_cost.toFixed(4)}</td>
                        <td className="px-3 py-2">
                          <span className={`text-xs ${tokenData.provider_status[provider] ? 'text-green-400' : 'text-red-400'}`}>
                            {tokenData.provider_status[provider] ? 'Available' : 'Unavailable'}
                          </span>
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