import { Download, Printer } from 'lucide-react'
import type { ScanResult } from '../types'

interface ReportExportProps {
  data: ScanResult
  scanId: string
}

export function ReportExport({ data, scanId }: ReportExportProps) {
  const handleExportJSON = () => {
    const exportData = {
      scan_id: data.scan_id,
      status: data.status,
      total_files: data.total_files,
      findings: (data?.findings || []).map(f => ({
        id: f.id,
        vulnerability_type: f.vulnerability_type,
        severity: f.severity,
        title: f.title,
        description: f.description,
        cwe_id: f.cwe_id,
        file_path: f.file_path,
        line_start: f.line_start,
        line_end: f.line_end,
        code_snippet: f.code_snippet,
        status: f.status,
        confidence: f.confidence,
        fix_suggestions: f.fix_suggestions?.map(fs => ({
          id: fs.id,
          title: fs.title,
          description: fs.description,
          code_before: fs.code_before,
          code_after: fs.code_after,
          language: fs.language,
        })),
      })),
      summary: data.summary,
      exported_at: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `codeguard-report-${scanId.substring(0, 8)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handlePrintPDF = () => {
    window.print()
  }

  return (
    <div className="flex items-center gap-2 print:hidden">
      <button
        onClick={handleExportJSON}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-bg-secondary border border-border-default text-text-secondary hover:text-text-primary hover:border-brand-500/30 transition-all"
        title="Export as JSON"
      >
        <Download className="w-3.5 h-3.5" />
        JSON
      </button>
      <button
        onClick={handlePrintPDF}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-bg-secondary border border-border-default text-text-secondary hover:text-text-primary hover:border-brand-500/30 transition-all"
        title="Print / Save as PDF"
      >
        <Printer className="w-3.5 h-3.5" />
        PDF
      </button>
    </div>
  )
}