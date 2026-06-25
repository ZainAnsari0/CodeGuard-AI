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
    } else {
      // Show error from scanStore or fallback
      setLocalError(result.error || 'Upload failed. Please try again.')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-surface-dim py-12 px-4">
      {/* Decorative ambient background */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none" />
      <div className="orb-cyan w-[400px] h-[400px] -top-32 -right-32 opacity-60" />
      <div className="orb-violet w-[500px] h-[500px] -bottom-48 -left-48 opacity-50" />

      {/* Main card */}
      <div className="relative z-10 w-full max-w-3xl animate-slide-up">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-display-lg gradient-text">New Scan</h1>
          <p className="text-body-md text-on-surface-variant mt-2">
            Upload code files to analyze for security vulnerabilities
          </p>
        </div>

        {/* Error banner */}
        {displayError && (
          <div className="flex items-start gap-3 p-4 rounded-xl mb-4 bg-severity-critical/10 border border-severity-critical/20 animate-fade-in">
            <AlertCircle className="w-5 h-5 text-severity-critical mt-0.5 shrink-0" />
            <p className="text-sm text-severity-critical">{displayError}</p>
          </div>
        )}

        {/* Glass card container */}
        <div className="glass-panel p-8 space-y-6">
          {/* Language selection */}
          <div>
            <label className="block text-label-md text-on-surface-variant mb-2 uppercase tracking-wider">
              Language / Framework
            </label>
            <div className="relative">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-surface-container-high border border-outline-variant
                  text-sm text-on-surface appearance-none cursor-pointer
                  focus:border-primary focus:shadow-glow-cyan-sm outline-none transition-all
                  hover:border-primary/40"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label} ({lang.extensions})
                  </option>
                ))}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-on-surface-variant" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Segmented tab control */}
          <div className="flex p-1.5 rounded-xl bg-surface-container-high border border-outline-variant/50">
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                ${activeTab === 'upload'
                  ? 'bg-surface-high text-primary shadow-card'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-highest/50'
                }`}
            >
              <Upload className="w-4 h-4" />
              Upload Files
            </button>
            <button
              onClick={() => setActiveTab('paste')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                ${activeTab === 'paste'
                  ? 'bg-surface-high text-primary shadow-card'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-highest/50'
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
              className={`relative rounded-2xl border-2 border-dashed p-10 text-center transition-all duration-200 cursor-pointer
                ${isDragging
                  ? 'border-primary bg-primary/5 shadow-glow-cyan scale-[1.01]'
                  : 'border-outline-variant hover:border-primary/40 hover:bg-surface-container/30'
                }`}
            >
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                accept=".py,.js,.jsx,.ts,.tsx,.java,.go,.rs,.c,.cpp,.h,.hpp,.swift,.zip"
              />

              <div className="flex flex-col items-center gap-4">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-200
                  ${isDragging
                    ? 'bg-primary/20 shadow-glow-cyan'
                    : 'bg-surface-container-high'
                  }`}
                >
                  <Upload className={`w-7 h-7 transition-colors ${isDragging ? 'text-primary' : 'text-on-surface-variant'}`} />
                </div>
                <div>
                  <p className="text-on-surface font-medium text-body-md">
                    {isDragging ? 'Drop files here' : 'Drag & drop files or click to browse'}
                  </p>
                  <p className="text-on-surface-variant text-body-sm mt-1.5">
                    Supports .py, .js, .ts, .java, .go, .rs, .c, .cpp, .h, .swift, .zip
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Paste code tab */}
          {activeTab === 'paste' && (
            <div className="space-y-3">
              <div className="rounded-2xl overflow-hidden border border-outline-variant">
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
                className="w-full py-2.5 rounded-xl border border-primary/40 text-sm font-medium text-primary
                  hover:bg-primary/10 hover:border-primary transition-all
                  disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent
                  flex items-center justify-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Add Code to Scan Queue
              </button>
            </div>
          )}

          {/* File queue list */}
          {files.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-label-md text-on-surface-variant uppercase tracking-wider">
                  {files.length} file{files.length !== 1 ? 's' : ''} selected
                </p>
                <button
                  onClick={() => setFiles([])}
                  className="text-label-sm text-on-surface-variant hover:text-severity-critical transition-colors"
                >
                  Clear all
                </button>
              </div>

              <div className="max-h-52 overflow-y-auto space-y-2 pr-1">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 rounded-xl bg-surface-container-high border border-outline-variant/40
                      group hover:border-primary/30 hover:bg-surface-high/50 transition-all duration-200"
                  >
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <FileCode className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-on-surface truncate font-medium">{file.name}</p>
                      <p className="text-xs text-on-surface-variant">{formatFileSize(file.size)}</p>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="p-1.5 rounded-lg text-on-surface-variant
                        hover:text-severity-critical hover:bg-severity-critical/10
                        transition-all opacity-0 group-hover:opacity-100"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gradient CTA button */}
          <button
            onClick={handleSubmit}
            disabled={isUploading || files.length === 0}
            className="w-full py-3.5 rounded-xl btn-gradient text-sm font-semibold flex items-center justify-center gap-2
              disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
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
    </div>
  )
}