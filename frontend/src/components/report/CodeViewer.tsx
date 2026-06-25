import { useRef, useEffect, useCallback, lazy, Suspense, Component, type ReactNode } from 'react'
import type { OnMount } from '@monaco-editor/react'
import type { editor as MonacoEditor } from 'monaco-editor'
import type { Finding } from '../../types'
import { SEVERITY_COLORS } from '../../utils/severity'

const Editor = lazy(() => import('@monaco-editor/react'))

interface CodeViewerProps {
  code: string
  language: string
  fileName: string
  findings: Finding[]
  activeFindingId: string | null
  onFindingClick?: (finding: Finding) => void
}

const SEVERITY_MARKER: Record<string, MonacoEditor.MarkerSeverity> = {
  critical: 8, // MarkerSeverity.Error
  high: 4,      // MarkerSeverity.Warning
  medium: 2,    // MarkerSeverity.Info
  low: 2,
  info: 2,
}

// ─── Error boundary that catches Monaco crashes and renders plain code ───

interface ErrorBoundaryState {
  hasError: boolean
}

class MonacoErrorBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode; fallback: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error) {
    console.warn('Monaco editor crashed, rendering fallback:', error.message)
  }

  render() {
    if (this.state.hasError) return this.props.fallback
    return this.props.children
  }
}

// ─── Simple fallback code viewer (no Monaco dependency) ───

function SimpleCodeViewer({
  code,
  findings,
  activeFindingId,
  onFindingClick,
}: {
  code: string
  findings: Finding[]
  activeFindingId: string | null
  onFindingClick?: (finding: Finding) => void
}) {
  const safeCode = typeof code === 'string' ? code : String(code ?? '')
  const lines = safeCode.split('\n')

  return (
    <div className="h-full overflow-auto bg-[#1e1e1e] text-[#d4d4d4] text-[13px] leading-[1.5] font-mono p-4">
      <table className="w-full border-collapse">
        <tbody>
          {lines.map((line, idx) => {
            const lineNum = idx + 1
            const lineFindings = findings.filter(
              (f) => f.line_start === lineNum || (f.line_start && f.line_end && lineNum >= f.line_start && lineNum <= f.line_end)
            )
            const isActive = lineFindings.some((f) => f.id === activeFindingId)
            const severity = lineFindings[0]?.severity || 'info'
            const bgClass = isActive
              ? 'bg-brand-500/15'
              : lineFindings.length > 0
                ? `${SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS]}/10`
                : ''

            return (
              <tr key={idx} className={bgClass}>
                <td className="select-none text-right pr-4 text-[#858585] w-12 align-top">
                  {lineNum}
                </td>
                <td className="align-top whitespace-pre">
                  {line || ' '}
                  {lineFindings.length > 0 && (
                    <span className="ml-2 inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-severity-critical/20 text-severity-critical cursor-pointer"
                      onClick={() => onFindingClick?.(lineFindings[0])}
                      title={`${lineFindings[0].vulnerability_type} (${lineFindings[0].severity})`}
                    >
                      {lineFindings[0].vulnerability_type}
                    </span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Main CodeViewer ───

export function CodeViewer({ code, language, fileName, findings, activeFindingId, onFindingClick }: CodeViewerProps) {
  const editorRef = useRef<MonacoEditor.IStandaloneCodeEditor | null>(null)
  const monacoRef = useRef<typeof import('monaco-editor') | null>(null)

  const handleEditorMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor
    monacoRef.current = monaco
    updateMarkers(editor, monaco, findings)
  }, [findings])

  // Update markers when findings change
  useEffect(() => {
    if (editorRef.current && monacoRef.current) {
      updateMarkers(editorRef.current, monacoRef.current, findings)
    }
  }, [findings, fileName])

  // Scroll to active finding
  useEffect(() => {
    if (!activeFindingId || !editorRef.current) return
    const finding = findings.find(f => f.id === activeFindingId)
    if (finding && finding.line_start) {
      editorRef.current.revealLineInCenter(finding.line_start)
    }
  }, [activeFindingId, findings])

  // Highlight active finding line
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current) return
    const editor = editorRef.current
    const monaco = monacoRef.current

    const activeFinding = findings.find(f => f.id === activeFindingId)
    if (!activeFinding || !activeFinding.line_start) {
      editor.deltaDecorations(editor.getModel()?.getAllDecorations()?.filter(d => d.options.className === 'active-finding-line').map(d => d.id) || [], [])
      return
    }

    editor.deltaDecorations([], [
      {
        range: new monaco.Range(activeFinding.line_start, 1, activeFinding.line_end || activeFinding.line_start, 1),
        options: {
          isWholeLine: true,
          className: 'active-finding-line',
          overviewRuler: {
            color: getSeverityColor(activeFinding.severity),
            position: monaco.editor.OverviewRulerLane.Full,
          },
        },
      },
    ])
  }, [activeFindingId, findings])

  const fallback = (
    <SimpleCodeViewer
      code={code}
      findings={findings}
      activeFindingId={activeFindingId}
      onFindingClick={onFindingClick}
    />
  )

  return (
    <div className="h-full rounded-xl overflow-hidden border border-border-default">
      <MonacoErrorBoundary fallback={fallback}>
        <Suspense fallback={<div className="h-64 flex items-center justify-center text-text-muted">Loading editor...</div>}>
          <Editor
            height="100%"
            language={language}
            theme="vs-dark"
            value={code}
            path={fileName}
            onMount={handleEditorMount}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 13,
              lineNumbers: 'on',
              padding: { top: 12 },
              wordWrap: 'on',
              renderLineHighlight: 'all',
              domReadOnly: true,
              contextmenu: false,
            }}
          />
        </Suspense>
      </MonacoErrorBoundary>
    </div>
  )
}

function updateMarkers(editor: MonacoEditor.IStandaloneCodeEditor, monaco: typeof import('monaco-editor'), findings: Finding[]) {
  const model = editor.getModel()
  if (!model) return

  const markers: MonacoEditor.IMarkerData[] = findings
    .filter(f => f.line_start && f.file_path === model.uri.path.split('/').pop())
    .map(f => ({
      severity: SEVERITY_MARKER[f.severity] ?? 2,
      message: `[${f.severity.toUpperCase()}] ${f.vulnerability_type}${f.cwe_id ? ` (CWE-${f.cwe_id})` : ''}`,
      startLineNumber: f.line_start ?? 1,
      startColumn: 1,
      endLineNumber: f.line_end ?? f.line_start ?? 1,
      endColumn: 1,
    }))

  monaco.editor.setModelMarkers(model, 'codeguard', markers)
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return '#ef4444'
    case 'high': return '#f97316'
    case 'medium': return '#eab308'
    case 'low': return '#3b82f6'
    default: return '#6b7280'
  }
}
