import { create } from 'zustand'
import type { Finding as FindingType } from '../types'
import { API_BASE_URL, unwrap } from '../lib/api'

export type ScanStatus = 'pending' | 'parsing' | 'analyzing' | 'completed' | 'failed'

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

  uploadFiles: async (files: File[], language: string) => {
    set({ isUploading: true, error: null })

    try {
      const formData = new FormData()
      files.forEach((file) => formData.append('files', file))
      formData.append('language', language)

      const response = await fetch(`${API_BASE_URL}/api/v1/scanner/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      if (!response.ok) {
        let errMsg = `Upload failed (HTTP ${response.status})`
        try {
          const raw = await response.json()
          errMsg = (raw as Record<string, unknown>).detail as string || (raw as Record<string, unknown>).message as string || errMsg
        } catch {
          // Response wasn't JSON — use status-based message
        }
        throw new Error(errMsg)
      }

      const text = await response.text()
      if (!text) throw new Error('Empty response from server')
      const raw = JSON.parse(text)

      const data = unwrap<{ scan_id: string; file_count: number; status: string }>(raw)

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
      const response = await fetch(`${API_BASE_URL}/api/v1/scanner/${scanId}/status`, {
        credentials: 'include',
        signal,
      })
      if (!response.ok) throw new Error('Status check failed')
      const text = await response.text()
      if (!text) return
      const data = unwrap<Record<string, unknown>>(JSON.parse(text))

      set({
        scanStatus: data.status as ScanStatus,
        progress: (data.progress as number) || 0,
        stage: (data.stage as string) || null,
        totalFiles: (data.total_files as number) || 0,
      })
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      set({ error: 'Network error while checking scan status' })
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
        await new Promise<void>((resolve) => {
          const timer = setTimeout(resolve, POLL_INTERVAL_MS)
          // Store timer so cancelPolling can clear it
          const state = get() as Record<string, unknown>
          state._currentTimer = timer
        })
        await poll()
      }
    }

    await poll()
  },

  cancelPolling: () => {
    const state = get() as Record<string, unknown>
    // Abort any in-flight fetch
    if (state._abortController && (state._abortController as AbortController)) {
      ;(state._abortController as AbortController).abort()
    }
    // Clear any pending timer
    if (state._currentTimer && typeof state._currentTimer === 'number') {
      clearTimeout(state._currentTimer as ReturnType<typeof setTimeout>)
    }
    set({ _abortController: null })
  },

  fetchScanResults: async (scanId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/scanner/${scanId}/results`, {
        credentials: 'include',
      })
      if (!response.ok) throw new Error('Failed to fetch results')
      const text = await response.text()
      if (!text) return
      const data = unwrap<Record<string, unknown>>(JSON.parse(text))

      set({
        findings: (data.findings as FindingType[]) || [],
        codeFiles: (data.code_files as Record<string, string>) || {},
        scanStatus: data.status as ScanStatus,
        totalFiles: (data.total_files as number) || 0,
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
    })
  },

  clearError: () => set({ error: null }),
}))