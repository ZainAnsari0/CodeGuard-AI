import { useState, useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Clock, CheckCircle, XCircle, Loader, Bug, ArrowRight,
  FileCode, Search, ChevronLeft, ChevronRight
} from 'lucide-react'
import { useScanHistory } from '../hooks/useScanResults'
import { SkeletonTable } from '../components/ui/Skeleton'
import type { ScanHistoryItem } from '../types'

const STATUS_CONFIG: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string; label: string }> = {
  completed: { icon: CheckCircle, color: 'text-success', label: 'Completed' },
  running: { icon: Loader, color: 'text-primary', label: 'Running' },
  pending: { icon: Clock, color: 'text-text-muted', label: 'Pending' },
  failed: { icon: XCircle, color: 'text-severity-critical', label: 'Failed' },
}

const STATUS_BADGE: Record<string, string> = {
  completed: 'badge-success',
  running: 'badge-low',
  pending: 'badge-info',
  failed: 'badge-critical',
}

const PAGE_SIZE = 10

export function ScanHistoryPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useScanHistory(0, 50)

  const items = (data?.items || []) as ScanHistoryItem[]
  const filtered = useMemo(() => {
    let result = statusFilter === 'all' ? items : items.filter(i => i.status === statusFilter)
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(i =>
        (i.branch || '').toLowerCase().includes(q) ||
        i.id.toLowerCase().includes(q)
      )
    }
    return result
  }, [items, statusFilter, search])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paged = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE
    return filtered.slice(start, start + PAGE_SIZE)
  }, [filtered, page])

  // Reset page when filter changes
  const handleFilterChange = (status: string) => {
    setStatusFilter(status)
    setPage(1)
  }

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
    <div className="space-y-5 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-headline-md font-semibold text-on-surface tracking-tight">Scan History</h1>
          <p className="text-body-sm text-on-surface-variant mt-1">View and manage your past security scans</p>
        </div>
        <Link
          to="/scan"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg btn-gradient text-label-md shadow-glow-cyan-sm shrink-0"
        >
          <Search className="w-4 h-4" />
          New Scan
        </Link>
      </div>

      {/* ── Filter bar with search ── */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        {/* Filter tabs */}
        <div className="flex gap-1 p-1 rounded-lg bg-surface-container-high">
          {['all', 'completed', 'running', 'failed'].map(status => (
            <button
              key={status}
              onClick={() => handleFilterChange(status)}
              className={`px-3 py-1.5 rounded-md text-label-sm transition-all ${
                statusFilter === status
                  ? 'bg-surface-bright text-primary shadow-sm border border-outline-variant/30'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {/* Search input */}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search by branch or ID..."
            className="w-full pl-9 pr-3 py-2 rounded-lg text-label-md input-glow text-on-surface placeholder:text-text-muted"
          />
        </div>

        <span className="text-label-sm text-text-muted ml-auto">{filtered.length} scan{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      {/* ── Content ── */}
      {isLoading ? (
        <SkeletonTable rows={5} cols={5} />
      ) : error ? (
        <div className="glass-card p-8 text-center">
          <Bug className="w-10 h-10 text-severity-critical mx-auto mb-3" />
          <p className="text-body-md text-on-surface-variant">Failed to load scan history</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-10 text-center">
          <FileCode className="w-14 h-14 text-text-muted mx-auto mb-4 opacity-40" />
          <p className="text-body-md text-on-surface-variant mb-4">No scans found</p>
          <Link to="/scan" className="text-label-md text-primary hover:text-brand-300 transition-colors">
            Start your first scan
          </Link>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-outline-variant/40">
                  <th className="text-left text-label-sm font-medium text-on-surface-variant tracking-wider px-5 py-3 uppercase">Scan</th>
                  <th className="text-left text-label-sm font-medium text-on-surface-variant tracking-wider px-5 py-3 uppercase">Status</th>
                  <th className="text-left text-label-sm font-medium text-on-surface-variant tracking-wider px-5 py-3 uppercase">Findings</th>
                  <th className="text-left text-label-sm font-medium text-on-surface-variant tracking-wider px-5 py-3 uppercase">Date</th>
                  <th className="text-right text-label-sm font-medium text-on-surface-variant tracking-wider px-5 py-3 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paged.map(item => {
                  const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending
                  const Icon = config.icon
                  const counts = getSeverityCounts(item)
                  const hasFindings = counts.critical + counts.high + counts.medium + counts.low > 0
                  const badgeClass = STATUS_BADGE[item.status] || 'badge-info'

                  return (
                    <tr key={item.id} className="border-b border-outline-variant/20 hover:bg-surface-high transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center">
                            <FileCode className="w-4 h-4 text-primary" />
                          </div>
                          <div>
                            <p className="text-label-md text-on-surface font-medium">{item.branch || 'Scan'}</p>
                            <p className="text-label-sm text-text-muted font-mono">{item.id.substring(0, 8)}...</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-label-sm font-medium ${badgeClass}`}>
                          <Icon className={`w-3.5 h-3.5 ${item.status === 'running' ? 'animate-spin' : ''}`} />
                          {config.label}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        {hasFindings ? (
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {counts.critical > 0 && <span className="badge-critical px-2 py-0.5 rounded text-label-sm font-mono font-medium">{counts.critical}C</span>}
                            {counts.high > 0 && <span className="badge-high px-2 py-0.5 rounded text-label-sm font-mono font-medium">{counts.high}H</span>}
                            {counts.medium > 0 && <span className="badge-medium px-2 py-0.5 rounded text-label-sm font-mono font-medium">{counts.medium}M</span>}
                            {counts.low > 0 && <span className="badge-low px-2 py-0.5 rounded text-label-sm font-mono font-medium">{counts.low}L</span>}
                          </div>
                        ) : (
                          <span className="text-label-sm text-text-muted font-mono">
                            {item.status === 'completed' ? '0 findings' : '—'}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-label-sm text-on-surface-variant">{formatDate(item.created_at)}</span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        {item.status === 'completed' && (
                          <button
                            onClick={() => navigate(`/scan/${item.id}/report`)}
                            className="inline-flex items-center gap-1.5 text-label-sm text-primary hover:text-brand-300 font-medium transition-colors group"
                          >
                            View Report <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
                          </button>
                        )}
                        {(item.status === 'running' || item.status === 'pending') && (
                          <button
                            onClick={() => navigate(`/scan/${item.id}/progress`)}
                            className="inline-flex items-center gap-1.5 text-label-sm text-primary hover:text-brand-300 font-medium transition-colors group"
                          >
                            Track <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
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
          <div className="md:hidden divide-y divide-outline-variant/20">
            {paged.map(item => {
              const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending
              const Icon = config.icon
              const badgeClass = STATUS_BADGE[item.status] || 'badge-info'

              return (
                <div key={item.id} className="p-4 hover:bg-surface-high transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-surface-container-high flex items-center justify-center">
                        <FileCode className="w-4 h-4 text-primary" />
                      </div>
                      <span className="text-label-md text-on-surface font-medium">{item.branch || 'Scan'}</span>
                    </div>
                    <span className={`inline-flex items-center gap-1 text-label-sm font-medium ${badgeClass} px-2 py-0.5 rounded-md`}>
                      <Icon className={`w-3 h-3 ${item.status === 'running' ? 'animate-spin' : ''}`} />
                      {config.label}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-label-sm text-text-muted">{formatDate(item.created_at)}</span>
                    {item.status === 'completed' && (
                      <button
                        onClick={() => navigate(`/scan/${item.id}/report`)}
                        className="text-label-sm text-primary hover:text-brand-300 font-medium flex items-center gap-1 group"
                      >
                        Report <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-outline-variant/40">
              <p className="text-label-sm text-on-surface-variant">
                Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-md hover:bg-surface-high transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4 text-on-surface-variant" />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 rounded-md text-label-sm font-medium transition-all ${
                      p === page
                        ? 'bg-surface-bright text-primary shadow-sm border border-outline-variant/30'
                        : 'text-on-surface-variant hover:bg-surface-high'
                    }`}
                  >
                    {p}
                  </button>
                ))}
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-1.5 rounded-md hover:bg-surface-high transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4 text-on-surface-variant" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}