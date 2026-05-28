import { useRef, useEffect, useCallback, lazy, Suspense } from 'react'
import type { OnMount } from '@monaco-editor/react'
import type { editor as MonacoEditor } from 'monaco-editor'
import type { Finding } from '../../types'

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

  return (
    <div className="h-full rounded-xl overflow-hidden border border-border-default">
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