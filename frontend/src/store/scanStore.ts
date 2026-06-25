import { create } from 'zustand'
import type { Finding as FindingType } from '../types'
import { apiClient } from '../shared/api/client'

export type ScanStatus = 'pending' | 'parsing' | 'analyzing' | 'running' | 'completed' | 'failed'

export type { FindingType as Finding }

// 10-minute scanner timeout at 2s intervals = 300 attempts, plus margin
const MAX_POLL_ATTEMPTS = 300
const POLL_INTERVAL_MS = 2000

export interface ScanState {
  currentScanId: string | null
  scanStatus: ScanStatus | null
  progress: number
  stage: string | null
  totalFiles: number
  findings: FindingType[]
  codeFiles: Record<string, string>
  isUploading: boolean
  error: string | null
  _abortController: AbortController | null
  _currentTimer: ReturnType<typeof setTimeout> | null

  uploadFiles: (files: File[], language: string) => Promise<{ success: boolean; scanId?: string; error?: string }>
  fetchScanStatus: (scanId: string, signal?: AbortSignal) => Promise<void>
  fetchScanResults: (scanId: string) => Promise<void>
  pollScanStatus: (scanId: string) => Promise<void>
  cancelPolling: () => void
  clearScan: () => void
  clearError: () => void
}

export const useScanStore = create<ScanState>()((set, get) => ({
  currentScanId: null,
  scanStatus: null,
  progress: 0,
  stage: null,
  totalFiles: 0,
  findings: [],
  codeFiles: {},
  isUploading: false,
  error: null,
  _abortController: null,
  _currentTimer: null,

  uploadFiles: async (files: File[], language: string) => {
    set({ isUploading: true, error: null })

    try {
      const formData = new FormData()
      files.forEach((file) => formData.append('files', file))
      formData.append('language', language)

      // Use apiClient.postForm() which includes 401 auto-refresh logic.
      // Previously used raw fetch() which bypassed token refresh, causing
      // "Upload failed (HTTP 401)" when the access token expired.
      const data = await apiClient.postForm<{ scan_id: string; file_count: number; status: string }>(
        '/api/v1/scanner/upload',
        formData,
      )

      set({
        currentScanId: data.scan_id,
        scanStatus: 'pending',
        totalFiles: data.file_count,
        isUploading: false,
      })

      return { success: true, scanId: data.scan_id }
    } catch (error: unknown) {
      set({
        isUploading: false,
        error: error instanceof Error ? error.message : 'Upload failed',
      })
      return { success: false, error: error instanceof Error ? error.message : 'Upload failed' }
    }
  },

   fetchScanStatus: async (scanId: string, signal?: AbortSignal) => {
     try {
       const data = await apiClient.get<Record<string, unknown>>(
         `/api/v1/scanner/${scanId}/status`,
       )

       set({
         scanStatus: data.status as ScanStatus,
         progress: (data.progress as number) || 0,
         stage: (data.stage as string) || null,
         totalFiles: (data.total_files as number) || 0,
         error: null,
       })
     } catch (err) {
       if (err instanceof DOMException && err.name === 'AbortError') return
       // Silently ignore 401 refresh redirects during polling
       if (err instanceof Error && err.message.includes('Session expired')) return
       // Use the actual error message when available
       const errorMsg = err instanceof Error ? err.message : 'Network error while checking scan status'
       set({ error: errorMsg })
     }
   },

  pollScanStatus: async (scanId: string) => {
    // Cancel any previous polling
    get().cancelPolling()

    const controller = new AbortController()
    set({ _abortController: controller })
    let attempts = 0

    const poll = async () => {
      if (attempts >= MAX_POLL_ATTEMPTS || controller.signal.aborted) {
        if (!controller.signal.aborted) {
          set({ error: 'Scan is taking too long. Check back later.' })
        }
        return
      }
      attempts++

      await get().fetchScanStatus(scanId, controller.signal)
      const status = get().scanStatus
      if (status && status !== 'completed' && status !== 'failed' && !controller.signal.aborted) {
        // Wait POLL_INTERVAL_MS before polling again
        const timer = setTimeout(() => {
          set({ _currentTimer: null })
          poll()
        }, POLL_INTERVAL_MS)
        set({ _currentTimer: timer })
      }
    }

    await poll()
  },

  cancelPolling: () => {
    const { _abortController, _currentTimer } = get()
    // Abort any in-flight fetch
    if (_abortController) {
      _abortController.abort()
    }
    // Clear any pending timer
    if (_currentTimer !== null) {
      clearTimeout(_currentTimer)
    }
    set({ _abortController: null, _currentTimer: null })
  },

   fetchScanResults: async (scanId: string) => {
     try {
       const data = await apiClient.get<Record<string, unknown>>(
         `/api/v1/scanner/${scanId}/results`,
       )

       set({
         findings: (data.findings as FindingType[]) || [],
         codeFiles: (data.code_files as Record<string, string>) || {},
         scanStatus: data.status as ScanStatus,
         totalFiles: (data.total_files as number) || 0,
         error: null,
       })
     } catch {
       set({ error: 'Network error while fetching scan results' })
     }
   },

  clearScan: () => {
    get().cancelPolling()
    set({
      currentScanId: null,
      scanStatus: null,
      progress: 0,
      stage: null,
      totalFiles: 0,
      findings: [],
      codeFiles: {},
      isUploading: false,
      error: null,
      _abortController: null,
      _currentTimer: null,
    })
  },

  clearError: () => set({ error: null }),
}))