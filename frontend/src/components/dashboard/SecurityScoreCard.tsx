import { Shield } from 'lucide-react'

interface SecurityScoreCardProps {
  securityScore: number
}

export function SecurityScoreCard({ securityScore }: SecurityScoreCardProps) {
  // Security score ring parameters
  const scoreRadius = 40
  const scoreCircumference = 2 * Math.PI * scoreRadius
  const scoreOffset = scoreCircumference - (securityScore / 100) * scoreCircumference
  const scoreColor = securityScore >= 80 ? '#10b981' : securityScore >= 60 ? '#eab308' : '#ef4444'

  return (
    <div className="glass-card p-5 flex flex-col items-center">
      <div className="flex items-center gap-2 mb-4 self-start">
        <Shield className="w-4 h-4 text-primary" />
        <h2 className="text-headline-sm font-semibold text-on-surface">Security Score</h2>
      </div>
      <div className="donut-chart mb-3">
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r={scoreRadius} fill="none" stroke="var(--color-surface-variant)" strokeWidth="8" />
          <circle cx="60" cy="60" r={scoreRadius} fill="none" stroke={scoreColor} strokeWidth="8"
            strokeDasharray={scoreCircumference} strokeDashoffset={scoreOffset}
            strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease-out' }} />
        </svg>
        <div className="donut-chart-label">
          <p className="text-display-xl font-bold text-on-surface">{securityScore || 0}</p>
          <p className="text-label-sm text-on-surface-variant uppercase tracking-wider">Score</p>
        </div>
      </div>
      <p className="text-label-sm text-on-surface-variant text-center">
        {securityScore >= 80 ? 'Excellent security posture' : securityScore >= 60 ? 'Some vulnerabilities found' : 'Critical issues need attention'}
      </p>
    </div>
  )
}
