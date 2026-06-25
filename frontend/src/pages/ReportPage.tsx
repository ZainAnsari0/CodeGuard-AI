import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  Shield, ArrowLeft, FileCode, Bug, AlertTriangle,
  CheckCircle, ChevronRight, Loader, RefreshCw, Home
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useScanResults } from '../hooks/useScanResults'
import { useAuthStore } from '../store/authStore'
import { apiClient } from '../shared/api/client'
import { CodeViewer } from '../components/report/CodeViewer'
import { FindingsPanel } from '../components/report/FindingsPanel'
import { FindingCard } from '../components/report/FindingCard'
import { ReportExport } from '../components/report/ReportExport'
import type { Finding } from '../types'
import { SEVERITY_COLORS, SEVERITY_BADGE_CLASSES, getLanguageFromFilename } from '../utils/severity'

export function ReportPage() {
  const { scanId } = useParams<{ scanId: string }>()
  const { user } = useAuthStore()
  const { data, isLoading, error } = useScanResults(scanId)

  const [activeFile, setActiveFile] = useState<string | null>(null)
  const [activeFinding, setActiveFinding] = useState<Finding | null>(null)
  const [mobileTab, setMobileTab] = useState<'code' | 'findings'>('findings')

  const fileNames = useMemo(() => Object.keys(data?.code_files || {}), [data])
  const currentFile = activeFile || fileNames[0] || ''
  const currentCode = data?.code_files?.[currentFile] || ''

  const currentFileFindings = useMemo(
    () => (data?.findings || []).filter(f => f.file_path === currentFile || f.file_path?.endsWith(currentFile)),
    [data?.findings, currentFile]
  )

  const language = useMemo(() => getLanguageFromFilename(currentFile), [currentFile])

  const counts = useMemo(() => {
    const c = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
    for (const f of data?.findings || []) {
      c[f.severity as keyof typeof c] = (c[f.severity as keyof typeof c] || 0) + 1
    }
    return c
  }, [data?.findings])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full bg-primary/10 animate-pulse-slow" />
            <Loader className="w-8 h-8 text-primary animate-spin absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          </div>
          <p className="text-body-md text-on-surface-variant">Loading scan results...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="glass-card p-8 text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-severity-critical mx-auto mb-4" />
          <h2 className="text-headline-sm font-semibold text-on-surface mb-2">Failed to Load Results</h2>
          <p className="text-body-sm text-on-surface-variant mb-4">{error?.message || 'Scan results could not be retrieved.'}</p>
          <Link to="/dashboard" className="text-label-md text-primary hover:text-brand-300 transition-colors">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-var(--spacing-header)-2rem)] animate-fade-in">
      {/* ── Breadcrumb header with severity badges ── */}
      <div className="glass-panel px-5 py-3 mb-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-b-none border-b-0">
        <div className="flex items-center gap-3">
          <Link to="/history" className="p-2 rounded-lg hover:bg-surface-high transition-colors text-on-surface-variant hover:text-on-surface">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <nav className="flex items-center gap-1.5 text-label-sm text-on-surface-variant">
            <Link to="/dashboard" className="hover:text-primary transition-colors flex items-center gap-1">
              <Home className="w-3 h-3" />
              Dashboard
            </Link>
            <ChevronRight className="w-3 h-3 opacity-40" />
            <Link to="/history" className="hover:text-primary transition-colors">History</Link>
            <ChevronRight className="w-3 h-3 opacity-40" />
            <span className="text-on-surface font-medium">Report</span>
          </nav>
          <span className="hidden sm:inline-block font-mono text-label-sm text-primary ml-1 bg-primary/10 px-2 py-0.5 rounded-md">
            {scanId?.substring(0, 8)}
          </span>
          {data.status === 'completed' && <CheckCircle className="w-4 h-4 text-success" />}
          {data.status === 'failed' && <AlertTriangle className="w-4 h-4 text-severity-critical" />}
        </div>

        {/* Severity summary */}
        <div className="flex items-center gap-3 flex-wrap">
          {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
            counts[sev] > 0 && (
              <span key={sev} className={`${SEVERITY_BADGE_CLASSES[sev]} px-2.5 py-1 rounded-md text-label-sm font-mono font-semibold`}>
                {counts[sev]} {sev.charAt(0).toUpperCase() + sev.slice(1)}
              </span>
            )
          ))}
          <span className="text-label-sm text-on-surface-variant ml-1">
            {(data?.findings || []).length} total
          </span>
          <div className="flex items-center gap-2 ml-2">
            <ReportExport data={data} scanId={scanId!} />
            <button
              onClick={async () => {
                try {
                  const result = await apiClient.post<{ new_analysis_id: string }>(
                    `/api/v1/scanner/${scanId}/rescan`,
                    {},
                  )
                  if (result.new_analysis_id) {
                    window.location.href = `/scan/${result.new_analysis_id}/progress`
                  }
                } catch {
                  // apiClient handles 401 auto-refresh; other errors silently ignored
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-label-sm font-medium bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 transition-all"
              title="Re-scan after applying fixes"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Re-scan
            </button>
          </div>
        </div>
      </div>

      {/* ── File tab bar ── */}
      {fileNames.length > 0 && (
        <div className="flex gap-1 overflow-x-auto px-5 py-2 bg-surface-low border-b border-outline-variant/30 scrollbar-thin">
          {fileNames.map(name => {
            const fileFindings = (data.findings || []).filter(f => f.file_path === name || f.file_path?.endsWith(name))
            const isActive = currentFile === name
            return (
              <button
                key={name}
                onClick={() => { setActiveFile(name); setActiveFinding(null); }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-label-sm font-medium whitespace-nowrap transition-all shrink-0
                  ${isActive
                    ? 'bg-surface-bright text-primary shadow-sm border border-primary/30'
                    : 'bg-surface-container text-on-surface-variant border border-outline-variant/30 hover:text-on-surface hover:bg-surface-high'
                  }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                <span className="font-mono">{name}</span>
                {fileFindings.length > 0 && (
                  <span className="ml-0.5 px-1.5 py-0.5 rounded text-label-sm font-mono badge-high">
                    {fileFindings.length}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}

      {/* ── Mobile tab toggle ── */}
      <div className="flex lg:hidden bg-surface-low border-b border-outline-variant/30">
        <button
          onClick={() => setMobileTab('findings')}
          className={`flex-1 py-2.5 text-label-md font-medium text-center transition-colors relative ${
            mobileTab === 'findings'
              ? 'text-primary'
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          Findings ({(data?.findings || []).length})
          {mobileTab === 'findings' && (
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-primary rounded-full" />
          )}
        </button>
        <button
          onClick={() => setMobileTab('code')}
          className={`flex-1 py-2.5 text-label-md font-medium text-center transition-colors relative ${
            mobileTab === 'code'
              ? 'text-primary'
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          Code
          {mobileTab === 'code' && (
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-primary rounded-full" />
          )}
        </button>
      </div>

      {/* ── Split-pane layout (55/45) ── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[55fr_45fr] min-h-0 overflow-hidden">
        {/* Left: Code viewer */}
        <div className={`min-h-0 overflow-hidden ${mobileTab !== 'code' ? 'hidden lg:flex lg:flex-col' : 'flex flex-col'}`}>
          {currentCode ? (
            <CodeViewer
              code={currentCode}
              language={language}
              fileName={currentFile}
              findings={currentFileFindings}
              activeFindingId={activeFinding?.id ?? null}
              onFindingClick={(f) => {
                setActiveFinding(f)
                setMobileTab('findings')
              }}
            />
          ) : (
            <div className="h-full glass-panel flex items-center justify-center m-2 rounded-lg">
              <div className="text-center">
                <FileCode className="w-14 h-14 text-text-muted mx-auto mb-3 opacity-40" />
                <p className="text-body-md text-on-surface-variant">No code available for display</p>
              </div>
            </div>
          )}
        </div>

        {/* Right: Findings panel */}
        <div className={`glass-panel rounded-l-none border-l-0 min-h-0 overflow-hidden flex flex-col
          ${mobileTab !== 'findings' ? 'hidden lg:flex' : 'flex'}`}
        >
          {activeFinding ? (
            <>
              <button
                onClick={() => setActiveFinding(null)}
                className="px-4 py-2.5 border-b border-outline-variant/30 text-label-sm text-primary hover:text-brand-300 flex items-center gap-1.5 transition-colors bg-surface-low"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back to findings
              </button>
              <div className="border-l-4"
                style={{ borderLeftColor: activeFinding.severity === 'critical' ? 'var(--color-severity-critical)' :
                  activeFinding.severity === 'high' ? 'var(--color-severity-high)' :
                  activeFinding.severity === 'medium' ? 'var(--color-severity-medium)' :
                  activeFinding.severity === 'low' ? 'var(--color-severity-low)' :
                  'var(--color-severity-info)'
                }}
              >
                <FindingCard
                  finding={activeFinding}
                  scanId={scanId!}
                />
              </div>
            </>
          ) : (
            <FindingsPanel
              findings={data?.findings || []}
              activeFindingId={activeFinding?.id ?? null}
              onFindingSelect={(f) => {
                setActiveFinding(f)
                const matchingFile = fileNames.find(name => f.file_path === name || f.file_path?.endsWith(name))
                if (matchingFile && matchingFile !== currentFile) {
                  setActiveFile(matchingFile)
                }
                setMobileTab('code')
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}