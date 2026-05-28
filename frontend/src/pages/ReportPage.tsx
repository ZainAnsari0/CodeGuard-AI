import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  Shield, ArrowLeft, FileCode, Bug, AlertTriangle,
  CheckCircle, Clock, ChevronRight, Loader, RefreshCw
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useScanResults } from '../hooks/useScanResults'
import { useAuthStore } from '../store/authStore'
import { CodeViewer } from '../components/report/CodeViewer'
import { FindingsPanel } from '../components/report/FindingsPanel'
import { FindingCard } from '../components/report/FindingCard'
import { ReportExport } from '../components/report/ReportExport'
import type { Finding } from '../types'
import { SEVERITY_COLORS, getLanguageFromFilename } from '../utils/severity'

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

  // Detect language from file extension
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
          <Loader className="w-8 h-8 text-brand-400 animate-spin mx-auto mb-4" />
          <p className="text-text-secondary">Loading scan results...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="glass-card p-8 text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-severity-critical mx-auto mb-4" />
          <h2 className="text-xl font-bold text-text-primary mb-2">Failed to Load Results</h2>
          <p className="text-text-secondary mb-4">{error?.message || 'Scan results could not be retrieved.'}</p>
          <Link to="/dashboard" className="text-brand-400 hover:text-brand-300 text-sm font-medium">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link to="/history" className="p-2 rounded-lg hover:bg-bg-tertiary transition-colors text-text-muted hover:text-text-primary">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Scan Report</h1>
            <p className="text-text-secondary text-sm mt-0.5">
              Scan <span className="font-mono text-brand-400">{scanId?.substring(0, 8)}...</span>
              {data.status === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-success inline ml-2" />}
              {data.status === 'failed' && <AlertTriangle className="w-3.5 h-3.5 text-severity-critical inline ml-2" />}
            </p>
          </div>
        </div>

        {/* Severity summary */}
        <div className="flex items-center gap-4">
          {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
            counts[sev] > 0 && (
              <div key={sev} className="text-center">
                <p className={`text-xl font-bold font-mono ${SEVERITY_COLORS[sev]}`}>{counts[sev]}</p>
                <p className="text-[10px] text-text-muted uppercase tracking-wider">{sev}</p>
              </div>
            )
          ))}
          <div className="text-center ml-2">
            <p className="text-xl font-bold font-mono text-text-primary">{data.findings.length}</p>
            <p className="text-[10px] text-text-muted uppercase tracking-wider">Total</p>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <ReportExport data={data} scanId={scanId!} />
            <button
              onClick={async () => {
                const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
                const res = await fetch(`${API_BASE_URL}/api/v1/scanner/${scanId}/rescan`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  credentials: 'include',
                })
                const result = await res.json()
                if (result.success && result.data?.new_analysis_id) {
                  window.location.href = `/scan/${result.data.new_analysis_id}/progress`
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-brand-500/10 border border-brand-500/30 text-brand-400 hover:bg-brand-500/20 transition-all"
              title="Re-scan after applying fixes"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Re-scan
            </button>
          </div>
        </div>
      </div>

      {/* File tabs */}
      {fileNames.length > 0 && (
        <div className="flex gap-1 overflow-x-auto pb-1">
          {fileNames.map(name => (
            <button
              key={name}
              onClick={() => { setActiveFile(name); setActiveFinding(null); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all
                ${currentFile === name
                  ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
                  : 'bg-bg-primary border border-border-default text-text-muted hover:text-text-secondary'}`}
            >
              <FileCode className="w-3.5 h-3.5" />
              {name}
              {(data.findings || []).filter(f => f.file_path === name || f.file_path?.endsWith(name)).length > 0 && (
                <span className="ml-1 px-1 py-0.5 rounded text-[10px] font-mono bg-severity-high/10 text-severity-high">
                  {(data.findings || []).filter(f => f.file_path === name || f.file_path?.endsWith(name)).length}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Mobile tab toggle */}
      <div className="flex lg:hidden border-b border-border-default">
        <button
          onClick={() => setMobileTab('findings')}
          className={`flex-1 py-2 text-sm font-medium text-center transition-colors ${
            mobileTab === 'findings'
              ? 'text-brand-400 border-b-2 border-brand-400'
              : 'text-text-muted hover:text-text-secondary'
          }`}
        >
          Findings ({data.findings.length})
        </button>
        <button
          onClick={() => setMobileTab('code')}
          className={`flex-1 py-2 text-sm font-medium text-center transition-colors ${
            mobileTab === 'code'
              ? 'text-brand-400 border-b-2 border-brand-400'
              : 'text-text-muted hover:text-text-secondary'
          }`}
        >
          Code
        </button>
      </div>

      {/* Main split-pane layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-4 min-h-[70vh]">
        {/* Left: Code viewer — hidden on mobile when on findings tab */}
        <div className={`min-h-[400px] ${mobileTab !== 'code' ? 'hidden lg:block' : ''}`}>
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
            <div className="h-full glass-card flex items-center justify-center">
              <div className="text-center">
                <FileCode className="w-12 h-12 text-text-muted mx-auto mb-3" />
                <p className="text-text-secondary">No code available for display</p>
              </div>
            </div>
          )}
        </div>

        {/* Right: Findings panel — hidden on mobile when on code tab */}
        <div className={`glass-card overflow-hidden flex flex-col min-h-[400px] ${mobileTab !== 'findings' ? 'hidden lg:flex' : ''}`}>
          {activeFinding ? (
            <>
              <button
                onClick={() => setActiveFinding(null)}
                className="px-4 py-2 border-b border-border-default text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 transition-colors"
              >
                <ArrowLeft className="w-3 h-3" /> Back to findings
              </button>
              <FindingCard
                finding={activeFinding}
                scanId={scanId!}
              />
            </>
          ) : (
            <FindingsPanel
              findings={data.findings}
              activeFindingId={activeFinding?.id ?? null}
              onFindingSelect={(f) => {
                setActiveFinding(f)
                // Switch to the file this finding is in
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