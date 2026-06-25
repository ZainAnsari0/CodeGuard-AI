import { LucideIcon } from 'lucide-react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface StatCardProps {
  title: string
  value: number
  change?: string
  trend?: string
  icon: LucideIcon
  color: string
  glowColor: string
  index: number
}

export function StatCard({
  title,
  value,
  change,
  trend,
  icon: Icon,
  color,
  glowColor,
  index,
}: StatCardProps) {
  const isTrendUp = trend === 'up'
  const isPositiveTrend = title === 'Vulnerabilities' ? !isTrendUp : isTrendUp

  return (
    <div
      className={`glass-card-hover stat-card-glow p-5 stagger-${index + 1}`}
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center ${glowColor}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        {change && (
          <div className={`flex items-center gap-1 text-label-sm font-medium ${
            isPositiveTrend ? 'text-success' : 'text-severity-critical'
          }`}>
            {isTrendUp ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            <span>{change}</span>
          </div>
        )}
      </div>
      <p className="text-display-xl font-bold text-on-surface">{(value ?? 0).toLocaleString()}</p>
      <p className="text-label-md text-on-surface-variant mt-0.5 uppercase tracking-wider">{title}</p>
    </div>
  )
}
