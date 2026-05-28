import { useState, useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Clock, CheckCircle, XCircle, Loader, Bug, ArrowRight,
  FileCode, Filter, Search
} from 'lucide-react'
import { useScanHistory } from '../hooks/useScanResults'
import { SkeletonTable } from '../components/ui/Skeleton'
import type { ScanHistoryItem } from '../types'

const STATUS_CONFIG: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string; label: string }> = {
  completed: { icon: CheckCircle, color: 'text-success', label: 'Completed' },
  running: { icon: Loader, color: 'text-brand-400', label: 'Running' },
  pending: { icon: Clock, color: 'text-text-muted', label: 'Pending' },
  failed: { icon: XCircle, color: 'text-severity-critical', label: 'Failed' },
}

export function ScanHistoryPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const { data, isLoading, error } = useScanHistory(0, 50)

  const items = (data?.items || []) as ScanHistoryItem[]
  const filtered = useMemo(() => {
    return statusFilter === 'all' ? items : items.filter(i => i.status === statusFilter)
  }, [items, statusFilter])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  }

  const getSeverityCounts = (item: ScanHistoryItem) => {
    const bySeverity = item.summary?.by_severity || {}
    return {
      critical: bySeverity.critical || 0,
      high: bySeverity.high || 0,
      medium: bySeverity.medium || 0,
      low: bySeverity.low || 0,
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Scan History</h1>
          <p className="text-text-secondary mt-1">View and manage your past security scans</p>
        </div>
        <Link
          to="/scan"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg btn-gradient text-sm font-medium shrink-0"
        >
          <Search className="w-4 h-4" />
          New Scan
        </Link>
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <Filter className="w-4 h-4 text-text-muted" />
        <div className="flex gap-1 p-1 rounded-lg bg-bg-primary border border-border-default">
          {['all', 'completed', 'running', 'failed'].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                statusFilter === status
                  ? 'bg-bg-tertiary text-text-primary shadow-sm'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
        <span className="text-xs text-text-muted">{filtered.length} scan{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      {isLoading ? (
        <SkeletonTable rows={5} cols={5} />
      ) : error ? (
        <div className="glass-card p-8 text-center">
          <p className="text-text-secondary">Failed to load scan history</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-8 text-center">
          <FileCode className="w-12 h-12 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary mb-4">No scans found</p>
          <Link to="/scan" className="text-brand-400 hover:text-brand-300 text-sm font-medium">
            Start your first scan
          </Link>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-default">
                  <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Scan</th>
                  <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Findings</th>
                  <th className="text-left text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Date</th>
                  <th className="text-right text-xs font-medium text-text-muted uppercase tracking-wider px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(item => {
                  const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending
                  const Icon = config.icon
                  const counts = getSeverityCounts(item)
                  const hasFindings = counts.critical + counts.high + counts.medium + counts.low > 0

                  return (
                    <tr key={item.id} className="border-b border-border-default/50 hover:bg-bg-card-hover transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-bg-tertiary flex items-center justify-center">
                            <FileCode className="w-4 h-4 text-brand-400" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-text-primary font-mono">{item.branch || 'Scan'}</p>
                            <p className="text-xs text-text-muted font-mono">{item.id.substring(0, 8)}...</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${config.color}`}>
                          <Icon className={`w-3.5 h-3.5 ${item.status === 'running' ? 'animate-spin' : ''}`} />
                          {config.label}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        {hasFindings ? (
                          <div className="flex items-center gap-1.5">
                            {counts.critical > 0 && <span className="badge-critical px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{counts.critical}C</span>}
                            {counts.high > 0 && <span className="badge-high px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{counts.high}H</span>}
                            {counts.medium > 0 && <span className="badge-medium px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{counts.medium}M</span>}
                            {counts.low > 0 && <span className="badge-low px-1.5 py-0.5 rounded text-[11px] font-mono font-medium">{counts.low}L</span>}
                          </div>
                        ) : (
                          <span className="text-xs text-text-muted font-mono">
                            {item.status === 'completed' ? '0 findings' : '—'}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-sm text-text-tertiary">{formatDate(item.created_at)}</span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        {item.status === 'completed' && (
                          <button
                            onClick={() => navigate(`/scan/${item.id}/report`)}
                            className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 font-medium transition-colors"
                          >
                            View Report <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {(item.status === 'running' || item.status === 'pending') && (
                          <button
                            onClick={() => navigate(`/scan/${item.id}/progress`)}
                            className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 font-medium transition-colors"
                          >
                            Track <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden divide-y divide-border-default/50">
            {filtered.map(item => {
              const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending
              const Icon = config.icon

              return (
                <div key={item.id} className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <FileCode className="w-4 h-4 text-brand-400" />
                      <span className="text-sm font-medium text-text-primary font-mono">{item.branch || 'Scan'}</span>
                    </div>
                    <span className={`inline-flex items-center gap-1 text-xs font-medium ${config.color}`}>
                      <Icon className={`w-3 h-3 ${item.status === 'running' ? 'animate-spin' : ''}`} />
                      {config.label}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-muted">{formatDate(item.created_at)}</span>
                    {item.status === 'completed' && (
                      <button
                        onClick={() => navigate(`/scan/${item.id}/report`)}
                        className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1"
                      >
                        Report <ArrowRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}