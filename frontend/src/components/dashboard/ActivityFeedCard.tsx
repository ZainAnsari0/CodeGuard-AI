import { Clock, LucideIcon } from 'lucide-react'

interface ActivityItem {
  type: string
  project: string
  time: string
  icon: LucideIcon
  color: string
}

interface ActivityFeedCardProps {
  activityFeed: ActivityItem[]
}

export function ActivityFeedCard({ activityFeed }: ActivityFeedCardProps) {
  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-headline-sm font-semibold text-on-surface">Activity</h2>
        </div>
      </div>

      <div className="space-y-3">
        {activityFeed.map((activity, index) => {
          const Icon = activity.icon
          return (
            <div key={index} className="flex items-start gap-3 group">
              <div
                className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                  activity.color === 'text-success'
                    ? 'bg-success/10'
                    : activity.color === 'text-severity-high'
                    ? 'bg-severity-high/10'
                    : activity.color === 'text-brand-400'
                    ? 'bg-brand-500/10'
                    : 'bg-accent-500/10'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${activity.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-body-sm text-on-surface leading-snug">
                  {activity.type === 'scan_completed' && 'Scan completed'}
                  {activity.type === 'vulnerability_found' && 'New vulnerabilities found'}
                  {activity.type === 'scan_started' && 'Scan started'}
                  {activity.type === 'project_added' && 'Project added'}
                </p>
                <p className="text-label-sm text-on-surface-variant mt-0.5 truncate">
                  {activity.project}
                </p>
              </div>
              <span className="text-label-sm text-on-surface-variant/60 whitespace-nowrap flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {activity.time}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
