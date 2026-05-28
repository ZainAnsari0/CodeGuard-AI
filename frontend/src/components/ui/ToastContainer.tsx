import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'

const variantConfig = {
  success: { icon: CheckCircle, border: 'border-success', text: 'text-success' },
  error: { icon: XCircle, border: 'border-severity-critical', text: 'text-severity-critical' },
  warning: { icon: AlertTriangle, border: 'border-warning', text: 'text-warning' },
  info: { icon: Info, border: 'border-brand-500', text: 'text-brand-400' },
} as const

export function ToastContainer() {
  const { toastQueue, removeToast } = useUIStore()

  if (toastQueue.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toastQueue.map((toast) => {
        const config = variantConfig[toast.variant]
        const Icon = config.icon
        return (
          <div
            key={toast.id}
            className={`glass-card flex items-start gap-3 p-4 border-l-4 ${config.border} animate-slide-in`}
          >
            <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${config.text}`} />
            <p className="text-sm text-text-primary flex-1">{toast.message}</p>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-text-muted hover:text-text-primary transition-colors shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}