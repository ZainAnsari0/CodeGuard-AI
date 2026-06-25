import { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Shield, FileCode, Bug, ArrowRight, CheckCircle, AlertTriangle, Loader,
  X, BookOpen, Eye, Zap, Lock, ChevronRight
} from 'lucide-react'
import { CodeViewer } from '../components/report/CodeViewer'
import { FindingsPanel } from '../components/report/FindingsPanel'
import { FindingCard } from '../components/report/FindingCard'
import type { Finding, ScanResult } from '../types'
import { SEVERITY_COLORS, SEVERITY_BADGE_CLASSES, getLanguageFromFilename } from '../utils/severity'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function GuestDemoPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<ScanResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeFile, setActiveFile] = useState<string | null>(null)
  const [activeFinding, setActiveFinding] = useState<Finding | null>(null)
  const [showBanner, setShowBanner] = useState(true)

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
      <div className="flex items-center justify-center min-h-screen bg-bg-primary grid-pattern">
        <div className="text-center space-y-3">
          <div className="relative inline-flex">
            <div className="absolute inset-0 rounded-full bg-brand-400/20 animate-ping" />
            <div className="relative w-12 h-12 rounded-full bg-surface-high flex items-center justify-center">
              <Shield className="w-6 h-6 text-brand-400 shield-logo" />
            </div>
          </div>
          <p className="text-body-md text-text-secondary">Loading demo scan results...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-primary grid-pattern">
        <div className="glass-panel p-8 text-center max-w-md space-y-4">
          <AlertTriangle className="w-12 h-12 text-severity-critical mx-auto" />
          <h2 className="text-headline-sm font-bold text-text-primary">Demo Unavailable</h2>
          <p className="text-body-sm text-text-secondary">{error || 'Could not load demo results.'}</p>
          <Link to="/login" className="btn-gradient inline-flex items-center gap-2 px-5 py-2 rounded-lg text-label-md">
            <Lock className="w-4 h-4" /> Sign in to scan your own code
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg-primary grid-pattern relative">
      {/* Decorative orbs */}
      <div className="orb-cyan w-[400px] h-[400px] -top-48 -left-48" />
      <div className="orb-violet w-[300px] h-[300px] top-1/3 -right-32" />

      {/* ─── Dismissible Demo Banner ─── */}
      {showBanner && (
        <div className="relative bg-brand-500/10 border-b border-brand-500/20 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 py-2.5 flex items-center justify-center gap-3">
            <Shield className="w-4 h-4 text-brand-400 shrink-0" />
            <p className="text-body-sm text-text-secondary">
              You're viewing a <span className="font-semibold text-brand-400">demo scan</span> with pre-computed results.
            </p>
            <Link
              to="/register"
              className="btn-gradient inline-flex items-center gap-1 px-3 py-1 rounded-md text-label-sm ml-2"
            >
              Sign up free <ArrowRight className="w-3 h-3" />
            </Link>
            <button
              onClick={() => setShowBanner(false)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
              aria-label="Dismiss banner"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ─── Minimal Public Header ─── */}
      <header className="border-b border-border-default bg-surface-dim/50 backdrop-blur-xl sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-brand-400 shield-logo" />
              <span className="text-headline-sm font-bold gradient-text">CodeGuard</span>
            </div>
            <div className="h-5 w-px bg-border-default mx-1" />
            <span className="text-label-sm text-text-muted">Demo Report</span>
          </div>

          <div className="flex items-center gap-4">
            {/* Severity counts */}
            <div className="hidden sm:flex items-center gap-3">
              {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
                counts[sev] > 0 && (
                  <div key={sev} className="text-center">
                    <p className={`text-label-md font-bold font-mono ${SEVERITY_COLORS[sev]}`}>{counts[sev]}</p>
                    <p className="text-[9px] text-text-muted uppercase tracking-wider">{sev}</p>
                  </div>
                )
              ))}
              <div className="h-6 w-px bg-border-default" />
              <div className="text-center">
                <p className="text-label-md font-bold font-mono text-text-primary">{(data?.findings || []).length}</p>
                <p className="text-[9px] text-text-muted uppercase tracking-wider">Total</p>
              </div>
            </div>

            <button
              onClick={() => navigate('/register')}
              className="btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-lg text-label-md"
            >
              <Zap className="w-3.5 h-3.5" /> Start Free Scan
            </button>
          </div>
        </div>
      </header>

      {/* ─── Main Content ─── */}
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-4 space-y-4">
        {/* File tabs */}
        {fileNames.length > 0 && (
          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
            {fileNames.map(name => {
              const fileFindings = (data.findings || []).filter(f => f.file_path === name || f.file_path?.endsWith(name))
              const isActive = currentFile === name
              return (
                <button
                  key={name}
                  onClick={() => { setActiveFile(name); setActiveFinding(null) }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-label-sm font-medium whitespace-nowrap transition-all ${
                    isActive
                      ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30 shadow-glow-cyan-sm'
                      : 'bg-surface-high/60 text-text-muted border border-transparent hover:text-text-secondary hover:bg-surface-high'
                  }`}
                >
                  <FileCode className="w-3.5 h-3.5" />
                  {name}
                  {fileFindings.length > 0 && (
                    <span className={`ml-1 px-1 py-0.5 rounded text-[10px] font-mono ${
                      fileFindings.some(f => f.severity === 'critical') ? 'badge-critical' :
                      fileFindings.some(f => f.severity === 'high') ? 'badge-high' :
                      'badge-medium'
                    }`}>
                      {fileFindings.length}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        )}

        {/* ─── Split Pane (3/5 code, 2/5 findings) ─── */}
        <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-4 min-h-[70vh]">
          {/* Code Viewer with vulnerability glow highlight */}
          <div className="min-h-[400px] relative">
            {currentCode ? (
              <div className="h-full rounded-xl overflow-hidden border border-border-default shadow-glow-cyan-sm">
                {/* Active finding indicator bar */}
                {activeFinding && (
                  <div className={`px-3 py-1.5 text-label-sm font-mono flex items-center gap-2 border-b ${
                    activeFinding.severity === 'critical' ? 'bg-severity-critical/10 border-severity-critical/20 text-severity-critical' :
                    activeFinding.severity === 'high' ? 'bg-severity-high/10 border-severity-high/20 text-severity-high' :
                    activeFinding.severity === 'medium' ? 'bg-severity-medium/10 border-severity-medium/20 text-severity-medium' :
                    'bg-brand-500/10 border-brand-500/20 text-brand-400'
                  }`}>
                    <Bug className="w-3.5 h-3.5" />
                    <span className="uppercase font-semibold">{activeFinding.severity}</span>
                    <span className="text-text-secondary">- {activeFinding.title || activeFinding.vulnerability_type}</span>
                    <span className="ml-auto text-text-muted">
                      {activeFinding.file_path}{activeFinding.line_start ? `:${activeFinding.line_start}` : ''}
                    </span>
                  </div>
                )}
                <CodeViewer
                  code={currentCode}
                  language={language}
                  fileName={currentFile}
                  findings={currentFileFindings}
                  activeFindingId={activeFinding?.id ?? null}
                  onFindingClick={setActiveFinding}
                />
              </div>
            ) : (
              <div className="h-full glass-panel flex items-center justify-center">
                <div className="text-center space-y-2">
                  <FileCode className="w-10 h-10 text-text-muted mx-auto" />
                  <p className="text-body-sm text-text-secondary">No code available for display</p>
                </div>
              </div>
            )}
          </div>

          {/* Findings Panel / Detail */}
          <div className="glass-panel overflow-hidden flex flex-col min-h-[400px]">
            {activeFinding ? (
              <>
                <button
                  onClick={() => setActiveFinding(null)}
                  className="px-4 py-2.5 border-b border-border-default text-label-sm text-brand-400 hover:text-brand-300 flex items-center gap-1 transition-colors bg-surface-high/30"
                >
                  <ChevronRight className="w-3 h-3 rotate-180" /> Back to findings
                </button>
                <FindingCard finding={activeFinding} scanId="demo" />
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
                }}
              />
            )}
          </div>
        </div>

        {/* ─── Upsell CTA Card ─── */}
        <div className="glass-panel p-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-brand-500/5 via-transparent to-accent-500/5 pointer-events-none" />
          <div className="relative flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center shrink-0 shadow-glow-cyan">
                <Bug className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-headline-sm font-bold text-text-primary">Ready to scan your own code?</h3>
                <p className="text-body-sm text-text-secondary mt-0.5">Sign up for free and get comprehensive security analysis of your projects.</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/register')}
              className="btn-gradient px-6 py-2.5 rounded-lg text-label-md whitespace-nowrap flex items-center gap-2 shrink-0"
            >
              Get Started Free <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}