import { useState } from 'react'
import {
  Bug, ExternalLink, Shield, Wrench, CheckCircle, Loader,
  AlertTriangle, BookOpen, ChevronDown, ChevronUp, X, Sparkles
} from 'lucide-react'
import { useAiExplanation, usePreviewFix, useApplyFix, useEnrichFinding } from '../../hooks/useScanResults'
import { useUIStore } from '../../store/uiStore'
import { DiffViewer } from './DiffViewer'
import type { Finding, AiExplanationResult } from '../../types'
import { SEVERITY_BADGE_CLASSES, getLanguageFromFilename } from '../../utils/severity'

interface FindingCardProps {
  finding: Finding
  scanId: string
}

export function FindingCard({ finding, scanId }: FindingCardProps) {
  const { addToast } = useUIStore()
  // If the finding already has an explanation from scan-time enrichment, show it immediately
  const [showExplanation, setShowExplanation] = useState(!!finding.explanation)
  const [showDiff, setShowDiff] = useState(false)

  const explainMutation = useAiExplanation()
  const previewFixMutation = usePreviewFix(scanId, finding.id)
  const applyFixMutation = useApplyFix(scanId, finding.id)
  const enrichMutation = useEnrichFinding(scanId, finding.id)

  const [explanation, setExplanation] = useState<AiExplanationResult | null>(finding.explanation ?? null)
  const [diffData, setDiffData] = useState<{ before: string; after: string } | null>(null)

  const handleExplain = async () => {
    // If already showing, toggle visibility
    if (showExplanation && explanation) {
      setShowExplanation(!showExplanation)
      return
    }

    // If finding has a pre-cached explanation from scan, use it without API call
    if (finding.explanation && !explanation) {
      setExplanation(finding.explanation)
      setShowExplanation(true)
      return
    }

    const language = finding.file_path ? getLanguageFromFilename(finding.file_path) : 'python'

    try {
      const result = await explainMutation.mutateAsync({
        vulnerability_type: finding.vulnerability_type,
        severity: finding.severity,
        cwe_id: finding.cwe_id,
        file_path: finding.file_path,
        code_snippet: finding.code_snippet,
        language,
        finding_id: finding.id,
      })
      setExplanation(result)
      setShowExplanation(true)
    } catch {
      addToast('Failed to generate explanation', 'error')
    }
  }

  const handleEnrich = async () => {
    try {
      await enrichMutation.mutateAsync()
      addToast('Finding enriched with AI analysis', 'success')
    } catch {
      addToast('Failed to enrich finding', 'error')
    }
  }

  const handlePreviewFix = async () => {
    // Check if finding already has a fix suggestion
    if (finding.fix_suggestions.length > 0) {
      const fix = finding.fix_suggestions[0]
      setDiffData({ before: fix.code_before || finding.code_snippet || '', after: fix.code_after || '' })
      setShowDiff(true)
      return
    }

    try {
      const result = await previewFixMutation.mutateAsync()
      setDiffData({ before: result.code_before || finding.code_snippet || '', after: result.code_after || '' })
      setShowDiff(true)
    } catch {
      addToast('Failed to generate fix preview', 'error')
    }
  }

  const handleApplyFix = async () => {
    try {
      await applyFixMutation.mutateAsync()
      addToast('Fix applied successfully', 'success')
      setShowDiff(false)
    } catch {
      addToast('Failed to apply fix', 'error')
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
            finding.severity === 'critical' ? 'bg-severity-critical/10' :
            finding.severity === 'high' ? 'bg-severity-high/10' :
            'bg-severity-medium/10'
          }`}>
            <Bug className={`w-5 h-5 ${
              finding.severity === 'critical' ? 'text-severity-critical' :
              finding.severity === 'high' ? 'text-severity-high' :
              'text-severity-medium'
            }`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`${SEVERITY_BADGE_CLASSES[finding.severity] || 'badge-info'} px-1.5 py-0.5 rounded text-[10px] font-mono font-medium uppercase`}>
                {finding.severity}
              </span>
              {finding.status === 'fixed' && (
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-success/10 text-success">FIXED</span>
              )}
              {finding.cvss_score && (
                <span className="text-xs text-text-muted font-mono">CVSS: {finding.cvss_score}</span>
              )}
            </div>
            <h3 className="text-sm font-semibold text-text-primary">{finding.title || finding.vulnerability_type}</h3>
            <p className="text-xs text-text-muted mt-0.5">
              {finding.file_path}{finding.line_start ? `:${finding.line_start}` : ''}
            </p>
          </div>
        </div>

        {/* Description */}
        {finding.description && (
          <p className="text-sm text-text-secondary leading-relaxed">{finding.description}</p>
        )}

        {/* CWE link */}
        {finding.cwe_id && (
          <a
            href={`https://cwe.mitre.org/data/definitions/${finding.cwe_id}.html`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            CWE-{finding.cwe_id}
          </a>
        )}

        {/* Confidence */}
        {finding.confidence != null && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-text-muted">Confidence</span>
              <span className="text-xs font-mono text-text-secondary">{finding.confidence}%</span>
            </div>
            <div className="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  finding.confidence >= 80 ? 'bg-success' :
                  finding.confidence >= 50 ? 'bg-severity-medium' :
                  'bg-severity-high'
                }`}
                style={{ width: `${finding.confidence}%` }}
              />
            </div>
          </div>
        )}

        {/* Code snippet */}
        {finding.code_snippet && (
          <div className="rounded-lg bg-bg-primary border border-border-default overflow-hidden">
            <div className="px-3 py-1.5 border-b border-border-default/50 text-xs text-text-muted">
              Vulnerable Code
            </div>
            <pre className="p-3 text-xs text-text-secondary overflow-x-auto font-mono leading-relaxed">
              {finding.code_snippet}
            </pre>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleExplain}
            disabled={explainMutation.isPending}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-500 text-xs font-medium text-brand-400
              hover:bg-brand-500/10 transition-all disabled:opacity-50"
          >
            {explainMutation.isPending ? (
              <Loader className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <BookOpen className="w-3.5 h-3.5" />
            )}
            {showExplanation ? 'Hide Explanation' : 'Explain'}
          </button>

          {/* Enrich button: only show for findings without pre-existing explanations */}
          {!finding.explanation && !explanation && (
            <button
              onClick={handleEnrich}
              disabled={enrichMutation.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-purple-500 text-xs font-medium text-purple-400
                hover:bg-purple-500/10 transition-all disabled:opacity-50"
            >
              {enrichMutation.isPending ? (
                <Loader className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              Enrich
            </button>
          )}

          {finding.status !== 'fixed' && (
            <>
              <button
                onClick={handlePreviewFix}
                disabled={previewFixMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-accent-500 text-xs font-medium text-accent-400
                  hover:bg-accent-500/10 transition-all disabled:opacity-50"
              >
                {previewFixMutation.isPending ? (
                  <Loader className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Shield className="w-3.5 h-3.5" />
                )}
                Preview Fix
              </button>

              {showDiff && diffData && (
                <button
                  onClick={handleApplyFix}
                  disabled={applyFixMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-success text-xs font-medium text-success
                    hover:bg-success/10 transition-all disabled:opacity-50"
                >
                  {applyFixMutation.isPending ? (
                    <Loader className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCircle className="w-3.5 h-3.5" />
                  )}
                  Apply Fix
                </button>
              )}
            </>
          )}
        </div>

        {/* AI Explanation panel */}
        {showExplanation && explanation && (
          <div className="space-y-3 animate-fade-in">
            <div className="rounded-lg bg-bg-primary border border-border-default p-4 space-y-3">
              {explanation.title && (
                <h4 className="text-sm font-semibold text-text-primary">{explanation.title}</h4>
              )}
              {explanation.description && (
                <div>
                  <h5 className="text-xs font-medium text-text-secondary mb-1">Description</h5>
                  <p className="text-xs text-text-secondary leading-relaxed">{explanation.description}</p>
                </div>
              )}
              {explanation.impact && (
                <div>
                  <h5 className="text-xs font-medium text-text-secondary mb-1">Impact</h5>
                  <p className="text-xs text-text-secondary leading-relaxed">{explanation.impact}</p>
                </div>
              )}
              {explanation.exploitation && (
                <div>
                  <h5 className="text-xs font-medium text-text-secondary mb-1">How It's Exploited</h5>
                  <p className="text-xs text-text-secondary leading-relaxed">{explanation.exploitation}</p>
                </div>
              )}
              {explanation.remediation && (
                <div>
                  <h5 className="text-xs font-medium text-text-secondary mb-1">Remediation</h5>
                  <p className="text-xs text-text-secondary leading-relaxed">{explanation.remediation}</p>
                </div>
              )}
              {explanation.references.length > 0 && (
                <div>
                  <h5 className="text-xs font-medium text-text-secondary mb-1">References</h5>
                  <ul className="space-y-1">
                    {explanation.references.map((ref, i) => (
                      <li key={i}>
                        <a href={ref} target="_blank" rel="noopener noreferrer" className="text-xs text-brand-400 hover:text-brand-300 break-all">
                          {ref}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {explanation.provider_used && (
                <p className="text-[10px] text-text-muted">Generated by: {explanation.provider_used}</p>
              )}
            </div>
          </div>
        )}

        {/* Diff viewer */}
        {showDiff && diffData && (
          <div className="space-y-3 animate-fade-in">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h4 className="text-xs font-semibold text-text-secondary">Fix Preview</h4>
                {/* AST validation badge */}
                {finding.fix_suggestions.length > 0 && finding.fix_suggestions[0]?.ast_validated != null && (
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-medium ${
                    finding.fix_suggestions[0].ast_validated
                      ? 'bg-success/10 text-success'
                      : 'bg-severity-high/10 text-severity-high'
                  }`}>
                    {finding.fix_suggestions[0].ast_validated ? 'AST Validated' : 'Validation Failed'}
                  </span>
                )}
                {/* Confidence score */}
                {finding.fix_suggestions.length > 0 && finding.fix_suggestions[0]?.confidence != null && (
                  <span className="text-[10px] text-text-muted font-mono">
                    Confidence: {Math.round((finding.fix_suggestions[0].confidence ?? 0) * 100)}%
                  </span>
                )}
              </div>
              <button onClick={() => setShowDiff(false)} className="p-1 rounded hover:bg-bg-tertiary text-text-muted">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <DiffViewer
              originalCode={diffData.before}
              fixedCode={diffData.after}
              language={finding.file_path ? getLanguageFromFilename(finding.file_path) : 'python'}
            />
          </div>
        )}
      </div>
    </div>
  )
}