import { useClassMetrics } from '../hooks/useInstructor'
import { useParams } from 'react-router-dom'
import { BarChart3, Users, FileCode, AlertTriangle, TrendingUp } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts'
import { SEVERITY_HEX_COLORS } from '../utils/severity'

const SEVERITY_COLORS = SEVERITY_HEX_COLORS

const SEVERITY_LABELS: Record<string, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
}

export function ClassMetricsPage() {
  const { classId } = useParams<{ classId: string }>()
  const { data: metrics, isLoading } = useClassMetrics(classId)

  if (isLoading) return <div className="glass-card p-8 text-center text-text-secondary">Loading metrics...</div>

  // Prepare severity data for BarChart
  const severityData = metrics?.findings_by_severity
    ? Object.entries(metrics.findings_by_severity).map(([sev, count]) => ({
        name: SEVERITY_LABELS[sev] || sev,
        count,
        fill: SEVERITY_COLORS[sev] || '#6b7280',
      }))
    : []

  // Prepare type data for BarChart
  const typeData = metrics?.top_vulnerability_types
    ? metrics.top_vulnerability_types.map((vt) => ({
        name: vt.type.length > 20 ? vt.type.substring(0, 20) + '...' : vt.type,
        fullName: vt.type,
        count: vt.count,
      }))
    : []

  // Prepare pie data from severity
  const pieData = severityData.map((d) => ({ name: d.name, value: d.count, fill: d.fill }))

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-text-primary">{metrics?.class_name || 'Class'} Metrics</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 text-center">
          <Users className="w-6 h-6 mx-auto text-primary mb-2" />
          <p className="text-2xl font-bold text-text-primary">{metrics?.total_students ?? 0}</p>
          <p className="text-sm text-text-muted">Students</p>
        </div>
        <div className="glass-card p-4 text-center">
          <FileCode className="w-6 h-6 mx-auto text-blue-400 mb-2" />
          <p className="text-2xl font-bold text-text-primary">{metrics?.total_scans ?? 0}</p>
          <p className="text-sm text-text-muted">Scans</p>
        </div>
        <div className="glass-card p-4 text-center">
          <AlertTriangle className="w-6 h-6 mx-auto text-orange-400 mb-2" />
          <p className="text-2xl font-bold text-text-primary">{metrics?.total_findings ?? 0}</p>
          <p className="text-sm text-text-muted">Findings</p>
        </div>
        <div className="glass-card p-4 text-center">
          <TrendingUp className="w-6 h-6 mx-auto text-green-400 mb-2" />
          <p className="text-2xl font-bold text-text-primary">{metrics?.avg_findings_per_student ?? 0}</p>
          <p className="text-sm text-text-muted">Avg/Student</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution — Bar Chart */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" /> Findings by Severity
          </h3>
          {severityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={severityData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#e2e8f0' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-text-secondary text-sm py-8 text-center">No severity data yet</p>
          )}
        </div>

        {/* Severity Breakdown — Pie Chart */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Severity Breakdown</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`pie-cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-text-secondary text-sm py-8 text-center">No severity data yet</p>
          )}
        </div>
      </div>

      {/* Top Vulnerability Types — Horizontal Bar */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">Top Vulnerability Types</h3>
        {typeData.length > 0 ? (
          <ResponsiveContainer width="100%" height={typeData.length * 40 + 30}>
            <BarChart data={typeData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <XAxis type="number" allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis dataKey="name" type="category" width={150} tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                formatter={(value: number, _name: string, props: { payload: { fullName: string } }) => [value, props.payload.fullName]}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-text-secondary text-sm py-4 text-center">No vulnerability data yet</p>
        )}
      </div>
    </div>
  )
}