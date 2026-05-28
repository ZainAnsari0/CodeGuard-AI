import { useNavigate } from 'react-router-dom'
import { Home, ArrowLeft, ShieldAlert, WifiOff, AlertTriangle, SearchX } from 'lucide-react'

interface ErrorPageProps {
  code: 404 | 403 | 500
  title?: string
  message?: string
}

const errorConfig: Record<number, { icon: typeof Home; title: string; message: string; color: string }> = {
  404: {
    icon: SearchX,
    title: 'Page Not Found',
    message: "The page you're looking for doesn't exist or has been moved.",
    color: 'text-blue-400',
  },
  403: {
    icon: ShieldAlert,
    title: 'Access Denied',
    message: "You don't have permission to access this page. Contact your administrator if you believe this is an error.",
    color: 'text-orange-400',
  },
  500: {
    icon: AlertTriangle,
    title: 'Server Error',
    message: 'Something went wrong on our end. Please try again later.',
    color: 'text-red-400',
  },
}

export function ErrorPage({ code, title, message }: ErrorPageProps) {
  const navigate = useNavigate()
  const config = errorConfig[code]
  const Icon = config.icon

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] animate-fade-in px-4">
      <div className="glass-card p-10 text-center max-w-md">
        <Icon className={`w-16 h-16 mx-auto mb-4 ${config.color}`} />
        <h1 className="text-6xl font-bold text-text-primary mb-2">{code}</h1>
        <h2 className="text-xl font-semibold text-text-primary mb-2">
          {title || config.title}
        </h2>
        <p className="text-text-secondary mb-6">
          {message || config.message}
        </p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => navigate(-1)} className="btn-secondary flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Go Back
          </button>
          <button onClick={() => navigate('/')} className="btn-primary flex items-center gap-2">
            <Home className="w-4 h-4" /> Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}

export function OfflinePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] animate-fade-in px-4">
      <div className="glass-card p-10 text-center max-w-md">
        <WifiOff className="w-16 h-16 mx-auto mb-4 text-text-muted" />
        <h1 className="text-2xl font-bold text-text-primary mb-2">You're Offline</h1>
        <p className="text-text-secondary mb-6">
          It looks like you've lost your internet connection. Check your network and try again.
        </p>
        <button onClick={() => window.location.reload()} className="btn-primary">
          Try Again
        </button>
      </div>
    </div>
  )
}