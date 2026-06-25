import { useMemo } from 'react'
import { useClassMetrics } from '../hooks/useInstructor'
import { useParams, Link } from 'react-router-dom'
import {
  BarChart3, Users, FileCode, AlertTriangle, TrendingUp,
  ArrowLeft, Download, Shield
} from 'lucide-react'
import { SEVERITY_HEX_COLORS } from '../utils/severity'

const SEVERITY_LABELS: Record<string, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
}

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info'] as const

/* ─── CSS-based vertical bar chart ─── */

function SeverityBarChart({ data }: { data: Array<{ name: string; count: number; fill: string }> }) {
  const maxCount = Math.max(...data.map(d => d.count), 1)

  return (
    <div className="flex items-end gap-3 h-[200px] px-2">
      {data.map(item => {
        const heightPct = (item.count / maxCount) * 100
        return (
          <div key={item.name} className="flex-1 flex flex-col items-center gap-2">
            <span className="text-label-sm font-mono text-text-primary">{item.count}</span>
            <div className="w-full relative flex-1 flex items-end">
              <div
                className="w-full rounded-t-md transition-all duration-700 ease-out"
                style={{
                  height: `${Math.max(heightPct, 2)}%`,
                  background: `linear-gradient(180deg, ${item.fill} 0%, ${item.fill}88 100%)`,
                  boxShadow: `0 0 12px ${item.fill}33`,
                }}
              />
            </div>
            <span className="text-label-sm text-text-muted">{item.name}</span>
          </div>
        )
      })}
    </div>
  )
}

/* ─── SVG donut chart ─── */

function DonutChart({ data }: { data: Array<{ name: string; value: number; fill: string }> }) {
  const total = data.reduce((sum, d) => sum + d.value, 0)
  const radius = 60
  const circumference = 2 * Math.PI * radius
  let cumulativeOffset = 0

  return (
    <div className="donut-chart" style={{ width: 200, height: 200 }}>
      <svg viewBox="0 0 160 160" width="200" height="200">
        {/* Background circle */}
        <circle
          cx="80" cy="80" r={radius}
          fill="none"
          stroke="var(--color-surface-variant)"
          strokeWidth="16"
        />
        {/* Data arcs */}
        {data.map((item, i) => {
          const segmentLength = total > 0 ? (item.value / total) * circumference : 0
          const offset = cumulativeOffset
          cumulativeOffset += segmentLength
          return (
            <circle
              key={i}
              cx="80" cy="80" r={radius}
              fill="none"
              stroke={item.fill}
              strokeWidth="16"
              strokeDasharray={`${segmentLength} ${circumference - segmentLength}`}
              strokeDashoffset={-offset}
              strokeLinecap="butt"
              className="transition-all duration-700"
            />
          )
        })}
      </svg>
      <div className="donut-chart-label">
        <p className="text-headline-md font-bold text-text-primary">{total}</p>
        <p className="text-label-sm text-text-muted">Total</p>
      </div>
    </div>
  )
}

/* ─── Main Page ─── */

export function ClassMetricsPage() {
  const { classId } = useParams<{ classId: string }>()
  const { data: metrics, isLoading } = useClassMetrics(classId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-body-sm text-text-muted">Loading metrics...</p>
        </div>
      </div>
    )
  }

  // Prepare severity data
  const severityData = metrics?.findings_by_severity
    ? Object.entries(metrics.findings_by_severity).map(([sev, count]) => ({
        name: SEVERITY_LABELS[sev] || sev,
        count: count as number,
        fill: SEVERITY_HEX_COLORS[sev] || '#6b7280',
        key: sev,
      }))
    : []

  // Ordered severity data for bar chart
  const orderedSeverityData = SEVERITY_ORDER
    .filter(sev => metrics?.findings_by_severity?.[sev])
    .map(sev => ({
      name: SEVERITY_LABELS[sev],
      count: (metrics?.findings_by_severity?.[sev] as number) || 0,
      fill: SEVERITY_HEX_COLORS[sev],
    }))

  // Prepare donut data from severity
  const pieData = severityData.map(d => ({ name: d.name, value: d.count, fill: d.fill }))

  // Prepare type data for horizontal bars
  const typeData = metrics?.top_vulnerability_types
    ? metrics.top_vulnerability_types.map(vt => ({
        name: vt.type.length > 25 ? vt.type.substring(0, 25) + '...' : vt.type,
        fullName: vt.type,
        count: vt.count,
      }))
    : []

  const maxTypeCount = Math.max(...typeData.map(d => d.count), 1)

  const handleExport = () => {
    if (!metrics) return
    const blob = new Blob([JSON.stringify(metrics, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${metrics.class_name || 'class'}-metrics.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6 animate-fade-in relative">
      {/* Decorative orbs */}
      <div className="orb-cyan w-[300px] h-[300px] -top-32 -right-32" />
      <div className="orb-violet w-[250px] h-[250px] bottom-0 -left-32" />

      {/* ─── Back link ─── */}
      <Link
        to="/classes"
        className="inline-flex items-center gap-1.5 text-label-md text-text-muted hover:text-brand-400 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Classes
      </Link>

      {/* ─── Header with export ─── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-display-lg font-bold text-text-primary tracking-tight flex items-center gap-3">
            <Shield className="w-7 h-7 text-brand-400" />
            {metrics?.class_name || 'Class'} Metrics
          </h1>
          <p className="text-body-sm text-text-secondary mt-1">Security analysis overview for your class</p>
        </div>
        <button
          onClick={handleExport}
          className="btn-secondary inline-flex items-center gap-2 px-4 py-2 rounded-lg text-label-md"
        >
          <Download className="w-4 h-4" /> Export JSON
        </button>
      </div>

      {/* ─── 4 Summary Stat Cards ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5" />}
          value={metrics?.total_students ?? 0}
          label="Students"
          colorClass="text-brand-400"
          glowColor="from-brand-400/20"
        />
        <StatCard
          icon={<FileCode className="w-5 h-5" />}
          value={metrics?.total_scans ?? 0}
          label="Scans"
          colorClass="text-accent-400"
          glowColor="from-accent-400/20"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          value={metrics?.total_findings ?? 0}
          label="Findings"
          colorClass="text-severity-high"
          glowColor="from-severity-high/20"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          value={metrics?.avg_findings_per_student ?? 0}
          label="Avg/Student"
          colorClass="text-success"
          glowColor="from-success/20"
        />
      </div>

      {/* ─── Charts Row ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution — CSS Bar Chart */}
        <div className="glass-card stat-card-glow p-6">
          <h3 className="text-headline-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-400" /> Findings by Severity
          </h3>
          {orderedSeverityData.length > 0 ? (
            <SeverityBarChart data={orderedSeverityData} />
          ) : (
            <div className="h-[200px] flex items-center justify-center">
              <p className="text-body-sm text-text-muted">No severity data yet</p>
            </div>
          )}
        </div>

        {/* Category Distribution — Donut Chart */}
        <div className="glass-card stat-card-glow p-6">
          <h3 className="text-headline-sm font-semibold text-text-primary mb-4">Category Distribution</h3>
          {pieData.length > 0 ? (
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <DonutChart data={pieData} />
              <div className="flex-1 space-y-2">
                {pieData.map((item, i) => (
                  <div key={i} className="flex items-center justify-between text-label-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-sm shrink-0"
                        style={{ backgroundColor: item.fill }}
                      />
                      <span className="text-text-secondary">{item.name}</span>
                    </div>
                    <span className="font-mono text-text-primary">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-[200px] flex items-center justify-center">
              <p className="text-body-sm text-text-muted">No severity data yet</p>
            </div>
          )}
        </div>
      </div>

      {/* ─── Top Vulnerability Types — Horizontal Bars with gradient ─── */}
      <div className="glass-card stat-card-glow p-6">
        <h3 className="text-headline-sm font-semibold text-text-primary mb-6">Top Vulnerability Types</h3>
        {typeData.length > 0 ? (
          <div className="space-y-4">
            {typeData.map((item, i) => {
              const widthPct = (item.count / maxTypeCount) * 100
              return (
                <div key={i} className="group">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-body-sm text-text-primary font-medium truncate max-w-[60%]" title={item.fullName}>
                      {item.name}
                    </span>
                    <span className="text-label-md font-mono text-brand-400">{item.count}</span>
                  </div>
                  <div className="h-3 rounded-full bg-surface-high overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-cyan-violet transition-all duration-700 ease-out"
                      style={{ width: `${Math.max(widthPct, 2)}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="py-8 text-center">
            <p className="text-body-sm text-text-muted">No vulnerability data yet</p>
          </div>
        )}
      </div>
    </div>
  )
}

/* ─── Stat Card Component ─── */

function StatCard({
  icon,
  value,
  label,
  colorClass,
  glowColor,
}: {
  icon: React.ReactNode
  value: number
  label: string
  colorClass: string
  glowColor: string
}) {
  return (
    <div className="glass-card stat-card-glow p-5 text-center group hover:bg-surface-high/40 transition-all">
      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${glowColor} to-transparent flex items-center justify-center mx-auto mb-3 ${colorClass}`}>
        {icon}
      </div>
      <p className="text-display-lg font-bold text-text-primary">{value}</p>
      <p className="text-label-sm text-text-muted mt-0.5">{label}</p>
    </div>
  )
}