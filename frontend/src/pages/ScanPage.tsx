import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileCode, X, Loader, AlertCircle, Code2 } from 'lucide-react'
import { useScanStore } from '../store/scanStore'
import { useAuthStore } from '../store/authStore'
import Editor from '@monaco-editor/react'

const SUPPORTED_LANGUAGES = [
  { value: 'python', label: 'Python', extensions: '.py' },
  { value: 'javascript', label: 'JavaScript', extensions: '.js, .jsx' },
  { value: 'typescript', label: 'TypeScript', extensions: '.ts, .tsx' },
  { value: 'java', label: 'Java', extensions: '.java' },
  { value: 'go', label: 'Go', extensions: '.go' },
  { value: 'rust', label: 'Rust', extensions: '.rs' },
  { value: 'c', label: 'C/C++', extensions: '.c, .cpp, .h' },
  { value: 'swift', label: 'Swift', extensions: '.swift' },
]

const LANGUAGE_EXTENSIONS: Record<string, string> = {
  python: 'py',
  javascript: 'js',
  typescript: 'ts',
  java: 'java',
  go: 'go',
  rust: 'rs',
  c: 'c',
  swift: 'swift',
}

export function ScanPage() {
  const navigate = useNavigate()
  const { uploadFiles, isUploading, error: scanError, clearError } = useScanStore()
  const { isAuthenticated } = useAuthStore()

  const [files, setFiles] = useState<File[]>([])
  const [language, setLanguage] = useState('python')
  const [isDragging, setIsDragging] = useState(false)
  const [localError, setLocalError] = useState('')
  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload')
  const [codeContent, setCodeContent] = useState('')

  const displayError = localError || scanError

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    setFiles(prev => [...prev, ...droppedFiles])
    clearError()
    setLocalError('')
  }, [clearError])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files)
      setFiles(prev => [...prev, ...selected])
      clearError()
      setLocalError('')
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUseCode = () => {
    if (!codeContent.trim()) {
      setLocalError('Please enter some code before adding')
      return
    }
    const ext = LANGUAGE_EXTENSIONS[language] || 'txt'
    const blob = new Blob([codeContent], { type: 'text/plain' })
    const file = new File([blob], `pasted-code.${ext}`, { type: 'text/plain' })
    setFiles(prev => [...prev, file])
    setCodeContent('')
    setLocalError('')
  }

  const handleSubmit = async () => {
    clearError()
    setLocalError('')

    if (files.length === 0) {
      setLocalError('Please select at least one file to scan')
      return
    }

    if (!isAuthenticated) {
      setLocalError('You must be logged in to scan files')
      return
    }

    const result = await uploadFiles(files, language)
    if (result.success && result.scanId) {
      navigate(`/scan/${result.scanId}/progress`)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">New Scan</h1>
        <p className="text-text-secondary mt-1">Upload code files to analyze for security vulnerabilities</p>
      </div>

      {displayError && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-severity-critical-bg border border-severity-critical/20 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-severity-critical mt-0.5 shrink-0" />
          <p className="text-sm text-severity-critical">{displayError}</p>
        </div>
      )}

      <div className="glass-card p-6 space-y-6">
        {/* Language selection */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">
            Primary Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-bg-primary border border-border-default text-sm text-text-primary
              focus:border-brand-500 focus:shadow-glow-cyan-sm outline-none transition-all"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label} ({lang.extensions})
              </option>
            ))}
          </select>
        </div>

        {/* Tab toggle */}
        <div className="flex gap-1 p-1 rounded-lg bg-bg-primary border border-border-default">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'upload'
                ? 'bg-bg-tertiary text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload Files
          </button>
          <button
            onClick={() => setActiveTab('paste')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'paste'
                ? 'bg-bg-tertiary text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            <Code2 className="w-4 h-4" />
            Paste Code
          </button>
        </div>

        {/* Upload tab */}
        {activeTab === 'upload' && (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer
              ${isDragging
                ? 'border-brand-500 bg-brand-500/5 shadow-glow-cyan-sm'
                : 'border-border-default hover:border-brand-400 hover:bg-bg-tertiary/30'
              }`}
          >
            <input
              type="file"
              multiple
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept=".py,.js,.jsx,.ts,.tsx,.java,.go,.rs,.c,.cpp,.h,.hpp,.swift,.zip"
            />
            <div className="flex flex-col items-center gap-3">
              <div className={`w-16 h-16 rounded-xl flex items-center justify-center transition-colors
                ${isDragging ? 'bg-brand-500/20' : 'bg-bg-tertiary'}`}>
                <Upload className={`w-8 h-8 transition-colors ${isDragging ? 'text-brand-400' : 'text-text-muted'}`} />
              </div>
              <div>
                <p className="text-text-primary font-medium">
                  {isDragging ? 'Drop files here' : 'Drag & drop files or click to browse'}
                </p>
                <p className="text-text-muted text-sm mt-1">
                  Supports .py, .js, .ts, .java, .go, .rs, .c, .cpp, .h, .swift, .zip
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Paste code tab */}
        {activeTab === 'paste' && (
          <div className="space-y-3">
            <div className="rounded-xl overflow-hidden border border-border-default">
              <Editor
                height="300px"
                language={language}
                theme="vs-dark"
                value={codeContent}
                onChange={(value) => setCodeContent(value || '')}
                options={{
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 13,
                  lineNumbers: 'on',
                  padding: { top: 12 },
                  wordWrap: 'on',
                  renderLineHighlight: 'all',
                }}
              />
            </div>
            <button
              onClick={handleUseCode}
              disabled={!codeContent.trim()}
              className="w-full py-2.5 rounded-lg border border-brand-500 text-sm font-medium text-brand-400
                hover:bg-brand-500/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed
                flex items-center justify-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Add Code to Scan Queue
            </button>
          </div>
        )}

        {/* File list */}
        {files.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-text-secondary">
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </p>
            <div className="max-h-48 overflow-y-auto space-y-1.5">
              {files.map((file, index) => (
                <div key={index} className="flex items-center gap-3 p-2.5 rounded-lg bg-bg-primary border border-border-default group">
                  <FileCode className="w-4 h-4 text-brand-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-text-primary truncate">{file.name}</p>
                    <p className="text-xs text-text-muted">{formatFileSize(file.size)}</p>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="p-1 rounded text-text-muted hover:text-severity-critical hover:bg-severity-critical-bg transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={isUploading || files.length === 0}
          className="w-full py-3 rounded-lg btn-gradient text-sm font-semibold flex items-center justify-center gap-2
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Uploading & Starting Scan...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Start Scan
            </>
          )}
        </button>
      </div>
    </div>
  )
}