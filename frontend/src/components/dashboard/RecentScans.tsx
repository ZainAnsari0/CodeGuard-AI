import { useNavigate } from 'react-router-dom'
import { FileCode, ChevronRight, CheckCircle, Activity, XCircle, ArrowRight, BarChart3 } from 'lucide-react'
import { SkeletonTable } from '../ui/Skeleton'
import { RecentAnalysis } from '../../types'

interface RecentScansProps {
  recentAnalyses: RecentAnalysis[]
  isLoading: boolean
}

export function RecentScans({ recentAnalyses, isLoading }: RecentScansProps) {
  const navigate = useNavigate()

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="badge-success inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-label-sm font-medium">
            <CheckCircle className="w-3 h-3" />Completed
          </span>
        )
      case 'running':
        return (
          <span className="badge-medium inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-label-sm font-medium">
            <Activity className="w-3 h-3 animate-pulse" />Running
          </span>
        )
      case 'failed':
        return (
          <span className="badge-critical inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-label-sm font-medium">
            <XCircle className="w-3 h-3" />Failed
          </span>
        )
      default:
        return (
          <span className="badge-info inline-flex items-center px-2.5 py-0.5 rounded-full text-label-sm font-medium">
            {status}
          </span>
        )
    }
  }

  if (isLoading) {
    return <SkeletonTable rows={4} cols={5} />
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-5 py-4 border-b border-outline-variant/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-primary" />
          <h2 className="text-headline-sm font-semibold text-on-surface">Recent Scans</h2>
        </div>
        <button
          onClick={() => navigate('/history')}
          className="text-label-md text-primary hover:text-brand-300 font-medium flex items-center gap-1 transition-colors"
        >
          View All <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-outline-variant/50">
              <th className="text-left text-label-sm text-on-surface-variant uppercase tracking-wider px-5 py-3">Project</th>
              <th className="text-left text-label-sm text-on-surface-variant uppercase tracking-wider px-5 py-3">Status</th>
              <th className="text-left text-label-sm text-on-surface-variant uppercase tracking-wider px-5 py-3">Severity</th>
              <th className="text-left text-label-sm text-on-surface-variant uppercase tracking-wider px-5 py-3">Last Scanned</th>
              <th className="text-right text-label-sm text-on-surface-variant uppercase tracking-wider px-5 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {recentAnalyses.map((scan) => {
              const displayName = scan.scan_name || scan.branch || 'Unknown'
              const critical = scan.summary?.by_severity?.critical || 0
              const high = scan.summary?.by_severity?.high || 0
              const medium = scan.summary?.by_severity?.medium || 0
              const low = scan.summary?.by_severity?.low || 0
              const lastScanned = scan.created_at
                ? new Date(scan.created_at).toLocaleDateString()
                : 'Unknown'

              return (
                <tr
                  key={scan.id}
                  className="border-b border-outline-variant/30 hover:bg-surface-high/30 hover:-translate-y-0.5 transition-all duration-200 cursor-pointer"
                  onClick={() =>
                    navigate(
                      scan.status === 'completed'
                        ? `/scan/${scan.id}/report`
                        : `/scan/${scan.id}/progress`
                    )
                  }
                >
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-surface-high flex items-center justify-center">
                        <FileCode className="w-4 h-4 text-primary" />
                      </div>
                      <span className="text-body-sm font-medium text-on-surface font-mono">
                        {displayName}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">{getStatusBadge(scan.status)}</td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      {critical > 0 && (
                        <span className="badge-critical inline-flex items-center px-1.5 py-0.5 rounded text-label-sm font-mono font-medium">
                          {critical}C
                        </span>
                      )}
                      {high > 0 && (
                        <span className="badge-high inline-flex items-center px-1.5 py-0.5 rounded text-label-sm font-mono font-medium">
                          {high}H
                        </span>
                      )}
                      {medium > 0 && (
                        <span className="badge-medium inline-flex items-center px-1.5 py-0.5 rounded text-label-sm font-mono font-medium">
                          {medium}M
                        </span>
                      )}
                      {low > 0 && (
                        <span className="badge-low inline-flex items-center px-1.5 py-0.5 rounded text-label-sm font-mono font-medium">
                          {low}L
                        </span>
                      )}
                      {scan.status === 'running' && (
                        <span className="text-label-sm text-on-surface-variant font-mono">--</span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-body-sm text-on-surface-variant">{lastScanned}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button className="text-on-surface-variant hover:text-primary transition-colors p-1">
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="md:hidden divide-y divide-outline-variant/30">
        {recentAnalyses.map((scan) => {
          const displayName = scan.scan_name || scan.branch || 'Unknown'
          const critical = scan.summary?.by_severity?.critical || 0
          const high = scan.summary?.by_severity?.high || 0
          const medium = scan.summary?.by_severity?.medium || 0
          const low = scan.summary?.by_severity?.low || 0
          const lastScanned = scan.created_at
            ? new Date(scan.created_at).toLocaleDateString()
            : 'Unknown'

          return (
            <div key={scan.id} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-surface-high flex items-center justify-center">
                    <FileCode className="w-4 h-4 text-primary" />
                  </div>
                  <span className="text-body-sm font-medium text-on-surface font-mono">
                    {displayName}
                  </span>
                </div>
                {getStatusBadge(scan.status)}
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  {critical > 0 && (
                    <span className="badge-critical px-1.5 py-0.5 rounded text-label-sm font-mono">
                      {critical}C
                    </span>
                  )}
                  {high > 0 && (
                    <span className="badge-high px-1.5 py-0.5 rounded text-label-sm font-mono">
                      {high}H
                    </span>
                  )}
                  {medium > 0 && (
                    <span className="badge-medium px-1.5 py-0.5 rounded text-label-sm font-mono">
                      {medium}M
                    </span>
                  )}
                  {low > 0 && (
                    <span className="badge-low px-1.5 py-0.5 rounded text-label-sm font-mono">
                      {low}L
                    </span>
                  )}
                </div>
                <span className="text-label-sm text-on-surface-variant">{lastScanned}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
