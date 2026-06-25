import { useState } from 'react'
import { useEventLogs } from '../hooks/useAdmin'
import { Shield, Filter, Search, ChevronLeft, ChevronRight, AlertTriangle, AlertCircle, Info, XCircle } from 'lucide-react'

export function EventLogsPage() {
  const [page, setPage] = useState(1)
  const [eventType, setEventType] = useState<string | undefined>(undefined)
  const [severity, setSeverity] = useState<string | undefined>(undefined)
  const [searchTerm, setSearchTerm] = useState('')
  const { data, isLoading } = useEventLogs(page, 50, eventType, severity)

  const severityConfig = (sev: string) => {
    const map: Record<string, { icon: typeof XCircle; cls: string; dotCls: string }> = {
      critical: { icon: XCircle, cls: 'badge-critical', dotCls: 'bg-red-400' },
      error: { icon: AlertCircle, cls: 'badge-high', dotCls: 'bg-orange-400' },
      warning: { icon: AlertTriangle, cls: 'badge-medium', dotCls: 'bg-yellow-400' },
      info: { icon: Info, cls: 'badge-info', dotCls: 'bg-slate-400' },
    }
    return map[sev] || { icon: Info, cls: 'badge-info', dotCls: 'bg-slate-400' }
  }

  const eventTypeIcon = (type: string) => {
    if (type.includes('login') || type.includes('auth')) return Shield
    return AlertCircle
  }

  const totalPages = Math.ceil((data?.total ?? 0) / 50)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="animate-slide-up">
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 rounded-lg bg-gradient-to-br from-red-500/20 to-amber-500/20 border border-red-500/20">
            <Shield className="w-5 h-5 text-primary" />
          </div>
          <h1 className="text-display-lg gradient-text">Security Event Logs</h1>
        </div>
        <p className="text-body-sm text-text-secondary ml-11">Audit trail and system event monitoring</p>
      </div>

      {/* Glass-panel Filter Bar */}
      <div className="glass-card p-4 animate-slide-up stagger-1">
        <div className="flex flex-col sm:flex-row gap-3 items-center">
          <div className="flex items-center gap-2 text-text-muted">
            <Filter className="w-4 h-4" />
            <span className="text-label-sm uppercase tracking-wider">Filters</span>
          </div>
          <div className="flex flex-1 flex-col sm:flex-row gap-3">
            <select
              value={eventType || ''}
              onChange={e => { setEventType(e.target.value || undefined); setPage(1) }}
              className="input-glow px-4 py-2.5 rounded-lg text-body-sm text-text-primary bg-surface-lowest appearance-none cursor-pointer"
            >
              <option value="">All Event Types</option>
              <option value="user_login">User Login</option>
              <option value="user_updated">User Updated</option>
              <option value="user_deactivated">User Deactivated</option>
              <option value="scan_completed">Scan Completed</option>
              <option value="scan_failed">Scan Failed</option>
              <option value="error">Error</option>
            </select>
            <select
              value={severity || ''}
              onChange={e => { setSeverity(e.target.value || undefined); setPage(1) }}
              className="input-glow px-4 py-2.5 rounded-lg text-body-sm text-text-primary bg-surface-lowest appearance-none cursor-pointer"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="text"
                placeholder="Search events..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="input-glow w-full pl-10 pr-4 py-2.5 rounded-lg text-body-sm text-text-primary placeholder:text-text-muted bg-surface-lowest"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Data Table */}
      {isLoading ? (
        <div className="glass-card p-12 text-center animate-slide-up stagger-2">
          <div className="inline-flex items-center gap-3 text-text-secondary">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            Loading events...
          </div>
        </div>
      ) : (
        <div className="glass-card overflow-hidden animate-slide-up stagger-2">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-light bg-surface-low/50">
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">Timestamp</th>
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">Event Type</th>
                  <th className="px-5 py-3.5 text-center text-label-sm text-text-muted uppercase tracking-wider font-medium">Severity</th>
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">Source</th>
                  <th className="px-5 py-3.5 text-left text-label-sm text-text-muted uppercase tracking-wider font-medium">Message</th>
                </tr>
              </thead>
              <tbody>
                {data?.events
                  ?.filter(e => !searchTerm || e.message?.toLowerCase().includes(searchTerm.toLowerCase()) || e.event_type?.toLowerCase().includes(searchTerm.toLowerCase()))
                  .map(event => {
                    const sevConfig = severityConfig(event.severity)
                    const TypeIcon = eventTypeIcon(event.event_type)
                    return (
                      <tr
                        key={event.id}
                        className="border-b border-border-light/50 hover:bg-surface-low/40 transition-all duration-200 hover:-translate-y-[2px]"
                      >
                        <td className="px-5 py-3.5 text-text-muted text-label-sm font-mono whitespace-nowrap">
                          {event.created_at ? new Date(event.created_at).toLocaleString() : '—'}
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-2">
                            <TypeIcon className="w-4 h-4 text-primary/70" />
                            <span className="text-text-primary font-medium text-label-sm font-mono">{event.event_type}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3.5 text-center">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-label-sm font-medium ${sevConfig.cls}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${sevConfig.dotCls}`} />
                            {event.severity}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-text-secondary text-label-sm">
                          {event.user_id ? (
                            <span className="font-mono text-primary/80">{event.user_id.slice(0, 8)}...</span>
                          ) : (
                            <span className="text-text-muted">System</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-text-secondary text-body-sm max-w-md truncate">
                          {event.message}
                        </td>
                      </tr>
                    )
                  })}
                {(!data?.events?.length) && (
                  <tr>
                    <td colSpan={5} className="px-5 py-12 text-center text-text-muted">
                      <Shield className="w-10 h-10 mx-auto mb-3 opacity-30" />
                      <p className="text-body-sm">No events found matching your filters</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-5 py-4 border-t border-border-light flex items-center justify-between">
            <span className="text-body-sm text-text-muted">
              <span className="text-text-secondary font-medium">{data?.total ?? 0}</span> total events
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="btn-secondary px-3 py-1.5 rounded-lg text-label-sm flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
              <span className="text-body-sm text-text-muted">
                Page <span className="text-text-primary font-medium">{page}</span> of <span className="text-text-primary font-medium">{totalPages || 1}</span>
              </span>
              <button
                disabled={(data?.events?.length ?? 0) < 50}
                onClick={() => setPage(p => p + 1)}
                className="btn-secondary px-3 py-1.5 rounded-lg text-label-sm flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}