import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useScanStore } from '../store/scanStore'
import {
  Loader, CheckCircle, AlertTriangle, FileCode,
  ArrowRight, Clock, Bug, Upload
} from 'lucide-react'

const STAGES = [
  { key: 'uploading', label: 'Uploading', icon: Upload },
  { key: 'parsing', label: 'Parsing Code', icon: FileCode },
  { key: 'analyzing', label: 'Analyzing Vulnerabilities', icon: Bug },
  { key: 'completed', label: 'Scan Complete', icon: CheckCircle },
]

export function ScanProgress() {
  const { scanId } = useParams<{ scanId: string }>()
  const navigate = useNavigate()
  const { scanStatus, progress, stage, totalFiles, fetchScanStatus, clearScan } = useScanStore()

  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!scanId) return
    if (scanStatus === 'completed' || scanStatus === 'failed') return

    const interval = setInterval(async () => {
      await fetchScanStatus(scanId)
    }, 3000)

    return () => clearInterval(interval)
  }, [scanId, scanStatus, fetchScanStatus])

  useEffect(() => {
    if (scanStatus === 'completed' || scanStatus === 'failed') return
    const timer = setInterval(() => setElapsed(prev => prev + 1), 1000)
    return () => clearInterval(timer)
  }, [scanStatus])

  useEffect(() => {
    if (scanStatus === 'completed') {
      const timeout = setTimeout(() => {
        navigate(`/scan/${scanId}/report`)
      }, 2000)
      return () => clearTimeout(timeout)
    }
  }, [scanStatus, scanId, navigate])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'completed': return 'text-success'
      case 'failed': return 'text-severity-critical'
      case 'running': return 'text-brand-400'
      default: return 'text-text-muted'
    }
  }

  const getStageIndex = () => {
    if (scanStatus === 'completed') return 3
    if (scanStatus === 'failed') return -1
    if (stage === 'analyzing') return 2
    if (stage === 'parsing') return 1
    return 0
  }

  const currentStageIndex = getStageIndex()

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Scan Progress</h1>
          <p className="text-text-secondary mt-1">Monitoring scan {scanId ? scanId.substring(0, 8) + '...' : ''}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Clock className="w-4 h-4" />
            <span className="font-mono">{formatTime(elapsed)}</span>
          </div>
          <span className={`text-sm font-medium ${getStatusColor(scanStatus)}`}>
            {scanStatus === 'running' ? 'Running' : scanStatus === 'completed' ? 'Completed' : scanStatus === 'failed' ? 'Failed' : 'Pending'}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="glass-card p-6">
        <div className="w-full bg-bg-tertiary rounded-full h-3 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-500 to-accent-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-xs text-text-muted">{Math.round(progress * 100)}%</span>
          <span className="text-xs text-text-muted">{totalFiles} file{totalFiles !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Stage indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STAGES.map((s, index) => {
          const StageIcon = s.icon
          const isActive = index === currentStageIndex
          const isCompleted = index < currentStageIndex
          const isPending = index > currentStageIndex

          return (
            <div
              key={s.key}
              className={`glass-card p-4 flex items-center gap-3 transition-all duration-300
                ${isActive ? 'ring-2 ring-brand-500 shadow-glow-cyan-sm' : ''}
                ${isCompleted ? 'opacity-70' : ''}
                ${isPending ? 'opacity-40' : ''}
              `}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0
                ${isCompleted ? 'bg-success/20' : isActive ? 'bg-brand-500/20' : 'bg-bg-tertiary'}`}
              >
                {isCompleted ? (
                  <CheckCircle className="w-5 h-5 text-success" />
                ) : isActive ? (
                  <Loader className="w-5 h-5 text-brand-400 animate-spin" />
                ) : (
                  <StageIcon className="w-5 h-5 text-text-muted" />
                )}
              </div>
              <div>
                <p className={`text-sm font-medium ${isCompleted ? 'text-success' : isActive ? 'text-text-primary' : 'text-text-muted'}`}>
                  {s.label}
                </p>
                {isActive && (
                  <p className="text-xs text-brand-400">In progress...</p>
                )}
                {isCompleted && (
                  <p className="text-xs text-success">Done</p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Error state */}
      {scanStatus === 'failed' && (
        <div className="glass-card p-6 border border-severity-critical/30">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-severity-critical shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-severity-critical">Scan Failed</h3>
              <p className="text-text-secondary mt-1">An error occurred during the scan. Please try again or contact support.</p>
              <button
                onClick={() => { clearScan(); navigate('/scan') }}
                className="mt-4 px-4 py-2 rounded-lg bg-severity-critical/10 text-severity-critical text-sm font-medium hover:bg-severity-critical/20 transition-colors"
              >
                Start New Scan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Completion state */}
      {scanStatus === 'completed' && (
        <div className="glass-card p-6 border border-success/30">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-6 h-6 text-success shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-success">Scan Complete!</h3>
              <p className="text-text-secondary mt-1">Your scan has finished processing. Results are being prepared.</p>
              <button
                className="mt-4 px-4 py-2 rounded-lg btn-gradient text-sm font-medium flex items-center gap-2"
                onClick={() => navigate(`/scan/${scanId}/report`)}
              >
                View Results <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}