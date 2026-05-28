import { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, FileCode, Bug, ArrowRight, CheckCircle, AlertTriangle, Loader } from 'lucide-react'
import { CodeViewer } from '../components/report/CodeViewer'
import { FindingsPanel } from '../components/report/FindingsPanel'
import { FindingCard } from '../components/report/FindingCard'
import type { Finding, ScanResult } from '../types'
import { SEVERITY_COLORS, getLanguageFromFilename } from '../utils/severity'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function GuestDemoPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<ScanResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeFile, setActiveFile] = useState<string | null>(null)
  const [activeFinding, setActiveFinding] = useState<Finding | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch(`${API_BASE_URL}/api/v1/guest/demo`)
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load demo: ${res.status}`)
        return res.json()
      })
      .then(raw => {
        if (!cancelled) {
          const result = raw?.data ?? raw
          setData(result)
        }
      })
      .catch(err => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => { cancelled = true }
  }, [])

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
      <div className="flex items-center justify-center min-h-screen bg-bg-primary">
        <div className="text-center">
          <Loader className="w-8 h-8 text-brand-400 animate-spin mx-auto mb-4" />
          <p className="text-text-secondary">Loading demo scan results...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-primary">
        <div className="glass-card p-8 text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-severity-critical mx-auto mb-4" />
          <h2 className="text-xl font-bold text-text-primary mb-2">Demo Unavailable</h2>
          <p className="text-text-secondary mb-4">{error || 'Could not load demo results.'}</p>
          <Link to="/login" className="text-brand-400 hover:text-brand-300 text-sm font-medium">
            Sign in to scan your own code
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Demo banner */}
      <div className="bg-brand-500/10 border-b border-brand-500/20 px-4 py-2 text-center">
        <p className="text-sm text-text-secondary">
          <Shield className="w-4 h-4 inline-block mr-1 text-brand-400" />
          You're viewing a <span className="font-semibold text-brand-400">demo scan</span> with pre-computed results.
          <Link to="/register" className="ml-2 text-brand-400 hover:text-brand-300 font-medium">
            Sign up to scan your own code <ArrowRight className="w-3 h-3 inline" />
          </Link>
        </p>
      </div>

      <div className="p-4 md:p-6 lg:p-8 space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-2xl font-bold text-text-primary">Demo Scan Report</h1>
              <p className="text-text-secondary text-sm mt-0.5">
                Sample scan showing common vulnerabilities
                <CheckCircle className="w-3.5 h-3.5 text-success inline ml-2" />
              </p>
            </div>
          </div>

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
          </div>
        </div>

        {/* File tabs */}
        {fileNames.length > 0 && (
          <div className="flex gap-1 overflow-x-auto pb-1">
            {fileNames.map(name => (
              <button
                key={name}
                onClick={() => { setActiveFile(name); setActiveFinding(null) }}
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

        {/* Main split-pane layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-4 min-h-[70vh]">
          <div className="min-h-[400px]">
            {currentCode ? (
              <CodeViewer
                code={currentCode}
                language={language}
                fileName={currentFile}
                findings={currentFileFindings}
                activeFindingId={activeFinding?.id ?? null}
                onFindingClick={setActiveFinding}
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

          <div className="glass-card overflow-hidden flex flex-col min-h-[400px]">
            {activeFinding ? (
              <>
                <button
                  onClick={() => setActiveFinding(null)}
                  className="px-4 py-2 border-b border-border-default text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 transition-colors"
                >
                  <ArrowRight className="w-3 h-3 rotate-180" /> Back to findings
                </button>
                <FindingCard finding={activeFinding} scanId="demo" />
              </>
            ) : (
              <FindingsPanel
                findings={data.findings}
                activeFindingId={activeFinding?.id ?? null}
                onFindingSelect={(f) => {
                  setActiveFinding(f)
                  const matchingFile = fileNames.find(name => f.file_path === name || f.file_path?.endsWith(name))
                  if (matchingFile && matchingFile !== currentFile) {
                    setActiveFile(matchingFile)
                  }
                }}
              />
            )}
          </div>
        </div>

        {/* CTA */}
        <div className="glass-card p-6 text-center">
          <Bug className="w-8 h-8 text-brand-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">Ready to scan your own code?</h3>
          <p className="text-text-secondary mb-4">Sign up for free and get comprehensive security analysis of your projects.</p>
          <button
            onClick={() => navigate('/register')}
            className="btn-primary px-6 py-2"
          >
            Get Started Free <ArrowRight className="w-4 h-4 inline ml-1" />
          </button>
        </div>
      </div>
    </div>
  )
}