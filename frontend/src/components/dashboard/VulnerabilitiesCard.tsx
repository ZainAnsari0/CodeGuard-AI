import { Bug } from 'lucide-react'
import { SEVERITY_BG_COLORS } from '../../utils/severity'

interface VulnerabilitiesCardProps {
  severityCounts: {
    critical: number
    high: number
    medium: number
    low: number
  }
}

export function VulnerabilitiesCard({ severityCounts }: VulnerabilitiesCardProps) {
  const totalVulns = severityCounts.critical + severityCounts.high + severityCounts.medium + severityCounts.low

  const severityData = [
    { label: 'Critical', count: severityCounts.critical, color: SEVERITY_BG_COLORS.critical, percentage: totalVulns ? Math.round((severityCounts.critical / totalVulns) * 100) : 0 },
    { label: 'High', count: severityCounts.high, color: SEVERITY_BG_COLORS.high, percentage: totalVulns ? Math.round((severityCounts.high / totalVulns) * 100) : 0 },
    { label: 'Medium', count: severityCounts.medium, color: SEVERITY_BG_COLORS.medium, percentage: totalVulns ? Math.round((severityCounts.medium / totalVulns) * 100) : 0 },
    { label: 'Low', count: severityCounts.low, color: SEVERITY_BG_COLORS.low, percentage: totalVulns ? Math.round((severityCounts.low / totalVulns) * 100) : 0 },
  ]

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-severity-critical" />
          <h2 className="text-headline-sm font-semibold text-on-surface">Vulnerabilities</h2>
        </div>
        <span className="text-label-sm text-on-surface-variant font-mono">{totalVulns} total</span>
      </div>

      <div className="space-y-4">
        {severityData.map((item) => (
          <div key={item.label}>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                <span className="text-body-sm text-on-surface-variant">{item.label}</span>
              </div>
              <span className="text-label-md font-medium text-on-surface font-mono">{item.count}</span>
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

      <div className="mt-5 pt-4 border-t border-outline-variant/50">
        <div className="grid grid-cols-4 gap-2">
          <div className="text-center">
            <p className="text-display-lg font-bold text-severity-critical font-mono">{severityCounts.critical}</p>
            <p className="text-label-sm text-on-surface-variant uppercase tracking-wider">Critical</p>
          </div>
          <div className="text-center">
            <p className="text-display-lg font-bold text-severity-high font-mono">{severityCounts.high}</p>
            <p className="text-label-sm text-on-surface-variant uppercase tracking-wider">High</p>
          </div>
          <div className="text-center">
            <p className="text-display-lg font-bold text-severity-medium font-mono">{severityCounts.medium}</p>
            <p className="text-label-sm text-on-surface-variant uppercase tracking-wider">Medium</p>
          </div>
          <div className="text-center">
            <p className="text-display-lg font-bold text-brand-400 font-mono">{severityCounts.low}</p>
            <p className="text-label-sm text-on-surface-variant uppercase tracking-wider">Low</p>
          </div>
        </div>
      </div>
    </div>
  )
}
