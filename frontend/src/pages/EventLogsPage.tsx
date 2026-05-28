import { useState } from 'react'
import { useEventLogs } from '../hooks/useAdmin'
import { Shield, Filter } from 'lucide-react'

export function EventLogsPage() {
  const [page, setPage] = useState(1)
  const [eventType, setEventType] = useState<string | undefined>(undefined)
  const [severity, setSeverity] = useState<string | undefined>(undefined)
  const { data, isLoading } = useEventLogs(page, 50, eventType, severity)

  const severityBadge = (sev: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500/20 text-red-400',
      error: 'bg-orange-500/20 text-orange-400',
      warning: 'bg-yellow-500/20 text-yellow-400',
      info: 'bg-blue-500/20 text-blue-400',
    }
    return <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[sev] || 'bg-surface-3 text-text-muted'}`}>{sev}</span>
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Shield className="w-6 h-6" /> Event Logs
        </h1>
        <p className="text-text-secondary mt-1">View audit logs and system events</p>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <Filter className="w-4 h-4 text-text-muted" />
        <select value={eventType || ''} onChange={e => { setEventType(e.target.value || undefined); setPage(1) }} className="input-field w-auto text-sm">
          <option value="">All Types</option>
          <option value="user_login">User Login</option>
          <option value="user_updated">User Updated</option>
          <option value="user_deactivated">User Deactivated</option>
          <option value="scan_completed">Scan Completed</option>
          <option value="scan_failed">Scan Failed</option>
          <option value="error">Error</option>
        </select>
        <select value={severity || ''} onChange={e => { setSeverity(e.target.value || undefined); setPage(1) }} className="input-field w-auto text-sm">
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="error">Error</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
      </div>

      {isLoading ? (
        <div className="glass-card p-8 text-center text-text-secondary">Loading events...</div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted text-left">
                  <th className="px-4 py-3 font-medium">Time</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Severity</th>
                  <th className="px-4 py-3 font-medium">Message</th>
                </tr>
              </thead>
              <tbody>
                {data?.events.map(event => (
                  <tr key={event.id} className="border-b border-border/50 hover:bg-surface-2/50">
                    <td className="px-4 py-3 text-text-muted text-xs whitespace-nowrap">
                      {event.created_at ? new Date(event.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-3 text-text-primary font-mono text-xs">{event.event_type}</td>
                    <td className="px-4 py-3">{severityBadge(event.severity)}</td>
                    <td className="px-4 py-3 text-text-secondary max-w-md truncate">{event.message}</td>
                  </tr>
                ))}
                {(!data?.events?.length) && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-text-muted">No events found</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-border flex items-center justify-between text-sm text-text-muted">
            <span>{data?.total ?? 0} total events</span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="btn-secondary text-xs">Previous</button>
              <button disabled={(data?.events?.length ?? 0) < 50} onClick={() => setPage(p => p + 1)} className="btn-secondary text-xs">Next</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}