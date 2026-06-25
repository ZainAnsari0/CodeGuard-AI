import { useNavigate } from 'react-router-dom'
import { Search, Upload, BarChart3 } from 'lucide-react'

export function QuickActions() {
  const navigate = useNavigate()

  const actions = [
    { label: 'New Scan', description: 'Analyze a new codebase', icon: Search, gradient: 'from-brand-400 to-brand-600', path: '/scan' },
    { label: 'Upload Code', description: 'Upload files for scanning', icon: Upload, gradient: 'from-accent-400 to-accent-600', path: '/scan' },
    { label: 'View Reports', description: 'Browse detailed reports', icon: BarChart3, gradient: 'from-brand-400 to-accent-500', path: '/history' },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {actions.map((action) => {
        const Icon = action.icon
        return (
          <button
            key={action.label}
            onClick={() => navigate(action.path)}
            className="glass-card-hover p-4 text-left group transition-all duration-200"
          >
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${action.gradient} flex items-center justify-center mb-3
              group-hover:shadow-glow-cyan transition-shadow duration-300`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <p className="text-body-sm font-medium text-on-surface group-hover:text-primary transition-colors">{action.label}</p>
            <p className="text-label-sm text-on-surface-variant mt-0.5">{action.description}</p>
          </button>
        )
      })}
    </div>
  )
}
