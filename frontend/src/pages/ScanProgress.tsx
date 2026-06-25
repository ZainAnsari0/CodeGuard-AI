import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useScanStore } from '../store/scanStore'
import {
  Shield, CheckCircle, AlertTriangle, FileCode,
  ArrowRight, Clock, Bug, Upload, Loader, X
} from 'lucide-react'

const STAGES = [
  { key: 'uploading', label: 'Uploading', icon: Upload },
  { key: 'parsing', label: 'Parsing', icon: FileCode },
  { key: 'analyzing', label: 'Analyzing', icon: Bug },
  { key: 'completed', label: 'Completed', icon: CheckCircle },
] as const

const LOG_LINES = [
  { ts: '00:00', msg: 'Initializing scan pipeline...' },
  { ts: '00:01', msg: 'Validating file integrity checksums...' },
  { ts: '00:02', msg: 'Building dependency graph...' },
  { ts: '00:04', msg: 'Running static analysis engine v3.2...' },
  { ts: '00:06', msg: 'Scanning for OWASP Top 10 patterns...' },
  { ts: '00:08', msg: 'Evaluating control-flow paths...' },
  { ts: '00:10', msg: 'Taint analysis in progress...' },
  { ts: '00:13', msg: 'Cross-referencing vulnerability database...' },
  { ts: '00:15', msg: 'Severity classification running...' },
  { ts: '00:17', msg: 'Generating remediation suggestions...' },
]

export function ScanProgress() {
   const { scanId } = useParams<{ scanId: string }>()
   const navigate = useNavigate()
   const { scanStatus, progress, stage, totalFiles, fetchScanStatus, clearScan, error } = useScanStore()

  const [elapsed, setElapsed] = useState(0)
  const [visibleLogs, setVisibleLogs] = useState<typeof LOG_LINES>([])
  const logContainerRef = useRef<HTMLDivElement>(null)

   // Poll scan status — stop on terminal states or error
   useEffect(() => {
     if (!scanId) return
     if (scanStatus === 'completed' || scanStatus === 'failed' || error) return

     // Call immediately
     void fetchScanStatus(scanId)

     const interval = setInterval(async () => {
       await fetchScanStatus(scanId)
     }, 3000)

     return () => clearInterval(interval)
   }, [scanId, scanStatus, fetchScanStatus])

  // Elapsed timer — pause when there's an error
  useEffect(() => {
    if (scanStatus === 'completed' || scanStatus === 'failed' || error) return
    const timer = setInterval(() => setElapsed(prev => prev + 1), 1000)
    return () => clearInterval(timer)
  }, [scanStatus, error])

  // Navigate on completion
  useEffect(() => {
    if (scanStatus === 'completed') {
      const timeout = setTimeout(() => {
        navigate(`/scan/${scanId}/report`)
      }, 2000)
      return () => clearTimeout(timeout)
    }
  }, [scanStatus, scanId, navigate])

  // Simulated log stream — pause when there's an error
  useEffect(() => {
    if (scanStatus === 'completed' || scanStatus === 'failed' || error) return
    const idx = visibleLogs.length
    if (idx >= LOG_LINES.length) return

    const delay = 1500 + Math.random() * 2000
    const timer = setTimeout(() => {
      setVisibleLogs(prev => [...prev, LOG_LINES[idx]])
    }, delay)
    return () => clearTimeout(timer)
  }, [visibleLogs.length, scanStatus])

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [visibleLogs])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const getStageIndex = () => {
    if (scanStatus === 'completed') return 3
    if (scanStatus === 'failed') return -1
    if (stage === 'analyzing') return 2
    if (stage === 'parsing') return 1
    return 0
  }

  const currentStageIndex = getStageIndex()

  const handleCancel = () => {
    clearScan()
    navigate('/scan')
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-surface-dim">
      {/* Decorative ambient background */}
      <div className="absolute inset-0 bg-grid-pattern animate-grid-move pointer-events-none" />
      <div className="orb-cyan w-[500px] h-[500px] -top-40 -left-40 animate-float" />
      <div className="orb-violet w-[600px] h-[600px] -bottom-60 -right-60" style={{ animationDelay: '-3s' }} />
      <div className="orb-cyan w-[300px] h-[300px] bottom-20 right-1/4 opacity-50" style={{ animationDelay: '-1.5s' }} />

      {/* Main content */}
      <div className="relative z-10 w-full max-w-2xl mx-auto px-6 py-12 animate-fade-in">
        {/* Header: Shield icon + title + timer */}
        <div className="flex flex-col items-center gap-4 mb-10">
          <div className="shield-logo">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center
              ${scanStatus === 'completed'
                ? 'bg-success/15 border border-success/30'
                : scanStatus === 'failed'
                  ? 'bg-severity-critical/15 border border-severity-critical/30'
                  : 'bg-primary/15 border border-primary/30'
              }`}
            >
              {scanStatus === 'completed' ? (
                <CheckCircle className="w-8 h-8 text-success" />
              ) : scanStatus === 'failed' ? (
                <AlertTriangle className="w-8 h-8 text-severity-critical" />
              ) : (
                <Shield className="w-8 h-8 text-primary" />
              )}
            </div>
          </div>

          <div className="text-center">
            <h1 className="text-display-lg gradient-text">
              {scanStatus === 'completed'
                ? 'Scan Complete'
                : scanStatus === 'failed'
                  ? 'Scan Failed'
                  : 'Scan in Progress'
              }
            </h1>
            <p className="text-body-md text-on-surface-variant mt-2">
              {scanId ? `ID: ${scanId.substring(0, 8)}...` : 'Initializing...'}
            </p>
          </div>

           {/* Elapsed timer badge — hidden on error */}
           {scanStatus !== 'completed' && scanStatus !== 'failed' && !error && (
             <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel">
               <Clock className="w-4 h-4 text-primary" />
               <span className="font-mono text-label-md text-primary">{formatTime(elapsed)}</span>
             </div>
           )}
         </div>

        {/* 4-stage pipeline stepper — hidden on error */}
        {!error && (
        <div className="glass-panel p-6 mb-6">
          <div className="flex items-start">
            {STAGES.map((s, index) => {
              const isActive = index === currentStageIndex
              const isCompleted = index < currentStageIndex
              const isPending = index > currentStageIndex

              return (
                <div key={s.key} className="pipeline-step">
                  {/* Connector line */}
                  {index > 0 && (
                    <div className={`h-0.5 flex-1 -mt-5 mb-3 transition-colors duration-500
                      ${isCompleted || isActive ? 'bg-gradient-to-r from-brand-500 to-accent-500' : 'bg-outline-variant'}
                    `} />
                  )}

                  {/* Circular step indicator */}
                  <div className={`
                    pipeline-step-indicator
                    ${isCompleted ? 'completed' : isActive ? 'active' : 'pending'}
                  `}>
                    {isCompleted ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : isActive ? (
                      <Loader className="w-5 h-5 animate-spin" />
                    ) : (
                      <s.icon className="w-5 h-5" />
                    )}
                  </div>

                  {/* Step label */}
                  <p className={`text-label-sm mt-2 text-center
                    ${isCompleted ? 'text-success' : isActive ? 'text-primary' : 'text-on-surface-variant'}
                  `}>
                    {s.label}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
        )}

        {/* Progress bar with shimmer — hidden on error */}
        {!error && (
        <div className="glass-panel p-6 mb-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-label-md text-on-surface-variant">
              {scanStatus === 'completed' ? 'Complete' : scanStatus === 'failed' ? 'Failed' : 'Progress'}
            </span>
            <span className="text-label-md font-mono text-primary">
              {Math.round(progress * 100)}%
            </span>
          </div>

          <div className="w-full h-3 rounded-full bg-surface-variant overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out relative"
              style={{
                width: `${Math.max(progress * 100, 2)}%`,
                background: 'linear-gradient(90deg, #06b6d4, #8b5cf6)',
              }}
            >
              {/* Shimmer overlay */}
              <div
                className="absolute inset-0 rounded-full"
                style={{
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent)',
                  backgroundSize: '200% 100%',
                  animation: 'shimmer 2s linear infinite',
                }}
              />
            </div>
          </div>

          <div className="flex justify-between mt-2">
            <span className="text-label-sm text-on-surface-variant">
              {totalFiles} file{totalFiles !== 1 ? 's' : ''}
            </span>
            {scanStatus === 'running' && (
              <span className="text-label-sm text-primary animate-pulse-slow">
                Processing...
              </span>
            )}
          </div>
        </div>
        )}

        {/* Live log stream — hidden on error */}
        {scanStatus !== 'completed' && scanStatus !== 'failed' && !error && visibleLogs.length > 0 && (
          <div className="glass-panel overflow-hidden mb-6">
            <div className="px-4 py-2.5 border-b border-glass-border flex items-center justify-between">
              <span className="text-label-sm text-on-surface-variant uppercase tracking-wider">
                Live Stream
              </span>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse-slow" />
                <span className="text-label-sm text-success">Active</span>
              </div>
            </div>

            <div
              ref={logContainerRef}
              className="relative max-h-48 overflow-y-auto px-4 py-3"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              {visibleLogs.map((log, i) => (
                <div key={i} className="flex items-start gap-3 py-1 text-sm animate-fade-in">
                  <span className="text-on-surface-variant shrink-0 text-label-sm select-none">
                    {log.ts}
                  </span>
                  <span className="text-primary">$</span>
                  <span className="text-on-surface">{log.msg}</span>
                </div>
              ))}

              {/* Fade-out gradient at bottom */}
              <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-[rgba(30,41,59,0.95)] to-transparent pointer-events-none" />
            </div>
          </div>
        )}

        {/* Completion state */}
        {scanStatus === 'completed' && (
          <div className="glass-panel p-6 border border-success/30 mb-6 animate-bounce-in">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-success shrink-0 mt-0.5" />
              <div>
                <h3 className="text-headline-sm text-success">Scan Complete!</h3>
                <p className="text-body-sm text-on-surface-variant mt-1">
                  Your scan has finished processing. Redirecting to results...
                </p>
                <button
                  className="mt-4 px-5 py-2.5 rounded-lg btn-gradient text-sm font-semibold flex items-center gap-2"
                  onClick={() => navigate(`/scan/${scanId}/report`)}
                >
                  View Results <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error state */}
        {scanStatus === 'failed' && (
          <div className="glass-panel p-6 border border-severity-critical/30 mb-6 animate-fade-in">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-severity-critical shrink-0 mt-0.5" />
              <div>
                <h3 className="text-headline-sm text-severity-critical">Scan Failed</h3>
                <p className="text-body-sm text-on-surface-variant mt-1">
                  An error occurred during the scan. Please try again or contact support.
                </p>
                <button
                  onClick={() => { clearScan(); navigate('/scan') }}
                  className="mt-4 px-5 py-2.5 rounded-lg btn-danger text-sm font-medium"
                >
                  Start New Scan
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Cancel / Retry button */}
        {error && (
          <div className="glass-panel p-6 border border-severity-critical/30 mb-6 animate-fade-in">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-severity-critical shrink-0 mt-0.5" />
              <div>
                <h3 className="text-headline-sm text-severity-critical">Connection Error</h3>
                <p className="text-body-sm text-on-surface-variant mt-1">
                  {error}
                </p>
                <div className="flex items-center gap-3 mt-4">
                  <button
                    onClick={() => {
                      clearScan()
                      navigate('/scan')
                    }}
                    className="px-5 py-2.5 rounded-lg btn-danger text-sm font-medium"
                  >
                    Start New Scan
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {!error && scanStatus !== 'completed' && scanStatus !== 'failed' && (
          <div className="flex justify-center">
            <button
              onClick={handleCancel}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium
                text-on-surface-variant border border-outline-variant
                hover:border-severity-critical/50 hover:text-severity-critical hover:bg-severity-critical/5
                transition-all duration-200"
            >
              <X className="w-4 h-4" />
              Cancel Scan
            </button>
          </div>
        )}
      </div>
    </div>
  )
}