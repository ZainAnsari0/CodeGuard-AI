import { useState } from 'react'
import { Bug, Filter, ChevronDown, ChevronUp } from 'lucide-react'
import type { Finding, FindingSeverity } from '../../types'
import { SEVERITY_BADGE_CLASSES } from '../../utils/severity'

interface FindingsPanelProps {
  findings: Finding[]
  activeFindingId: string | null
  onFindingSelect: (finding: Finding) => void
}

const SEVERITY_ORDER: FindingSeverity[] = ['critical', 'high', 'medium', 'low', 'info']

export function FindingsPanel({ findings, activeFindingId, onFindingSelect }: FindingsPanelProps) {
  const [filterSeverity, setFilterSeverity] = useState<FindingSeverity | 'all'>('all')
  const [sortBy, setSortBy] = useState<'severity' | 'file' | 'type'>('severity')
  const [sortAsc, setSortAsc] = useState(false)

  const filtered = findings
    .filter(f => filterSeverity === 'all' || f.severity === filterSeverity)
    .sort((a, b) => {
      const mult = sortAsc ? 1 : -1
      if (sortBy === 'severity') {
        return (SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)) * mult
      }
      if (sortBy === 'file') {
        return a.file_path.localeCompare(b.file_path) * mult
      }
      return a.vulnerability_type.localeCompare(b.vulnerability_type) * mult
    })

  const counts = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1
    return acc
  }, {})

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border-default flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-severity-critical" />
          <h3 className="text-sm font-semibold text-text-primary">
            Findings <span className="text-text-muted font-normal">({findings.length})</span>
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-text-muted" />
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value as FindingSeverity | 'all')}
            className="text-xs bg-bg-primary border border-border-default rounded px-2 py-1 text-text-secondary outline-none"
          >
            <option value="all">All</option>
            {SEVERITY_ORDER.map(s => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)} ({counts[s] || 0})</option>
            ))}
          </select>
        </div>
      </div>

      {/* Sort bar */}
      <div className="px-4 py-2 border-b border-border-default/50 flex items-center gap-3 text-xs text-text-muted">
        <span>Sort:</span>
        {(['severity', 'file', 'type'] as const).map(key => (
          <button
            key={key}
            onClick={() => { if (sortBy === key) setSortAsc(!sortAsc); else { setSortBy(key); setSortAsc(false); } }}
            className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded transition-colors ${sortBy === key ? 'text-brand-400 bg-brand-500/10' : 'hover:text-text-secondary'}`}
          >
            {key.charAt(0).toUpperCase() + key.slice(1)}
            {sortBy === key && (sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
          </button>
        ))}
      </div>

      {/* Findings list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="p-6 text-center text-text-muted text-sm">No findings match the filter</div>
        ) : (
          filtered.map(finding => (
            <button
              key={finding.id}
              onClick={() => onFindingSelect(finding)}
              className={`w-full text-left p-3 border-b border-border-default/30 transition-colors
                ${activeFindingId === finding.id ? 'bg-brand-500/10 border-l-2 border-l-brand-500' : 'hover:bg-bg-card-hover'}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`${SEVERITY_BADGE_CLASSES[finding.severity] || 'badge-info'} px-1.5 py-0.5 rounded text-[10px] font-mono font-medium uppercase`}>
                  {finding.severity}
                </span>
                {finding.status === 'fixed' && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-success/10 text-success">FIXED</span>
                )}
                <span className="text-xs text-text-muted font-mono ml-auto">
                  {finding.cwe_id ? `CWE-${finding.cwe_id}` : ''}
                </span>
              </div>
              <p className="text-sm font-medium text-text-primary truncate">{finding.title || finding.vulnerability_type}</p>
              <p className="text-xs text-text-muted truncate mt-0.5">{finding.file_path}{finding.line_start ? `:${finding.line_start}` : ''}</p>
            </button>
          ))
        )}
      </div>
    </div>
  )
}