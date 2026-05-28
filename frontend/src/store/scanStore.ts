import { create } from 'zustand'
import type { Finding as FindingType } from '../types'
import { API_BASE_URL, unwrap } from '../lib/api'

export type ScanStatus = 'pending' | 'parsing' | 'analyzing' | 'completed' | 'failed'

export type { FindingType as Finding }

const MAX_POLL_ATTEMPTS = 90 // ~3 minutes at 2s intervals

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

  uploadFiles: (files: File[], language: string) => Promise<{ success: boolean; scanId?: string; error?: string }>
  fetchScanStatus: (scanId: string) => Promise<void>
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

      const raw = await response.json()

      if (!response.ok) {
        const rawObj = raw as Record<string, unknown>
        const errMsg = (rawObj.detail as string) || (rawObj.message as string) || 'Upload failed'
        throw new Error(errMsg)
      }

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

  fetchScanStatus: async (scanId: string) => {
    try {
      const data = await unwrap<Record<string, unknown>>(
        fetch(`${API_BASE_URL}/api/v1/scanner/${scanId}/status`, { credentials: 'include' })
          .then(async (res) => { if (!res.ok) throw new Error('Status check failed'); return res.json() })
      )

      set({
        scanStatus: data.status as ScanStatus,
        progress: (data.progress as number) || 0,
        stage: (data.stage as string) || null,
        totalFiles: (data.total_files as number) || 0,
      })
    } catch {
      set({ error: 'Network error while checking scan status' })
    }
  },

  pollScanStatus: async (scanId: string) => {
    get().cancelPolling()
    let attempts = 0
    const timers: ReturnType<typeof setTimeout>[] = []

    const poll = async () => {
      if (attempts >= MAX_POLL_ATTEMPTS) {
        set({ error: 'Scan is taking too long. Check back later.' })
        return
      }
      attempts++

      await get().fetchScanStatus(scanId)
      const status = get().scanStatus
      if (status && status !== 'completed' && status !== 'failed') {
        const timer = setTimeout(poll, 2000)
        timers.push(timer)
        // Also store on instance for cleanup
        ;(get() as Record<string, unknown>)._pollTimers = timers
      }
    }
    ;(get() as Record<string, unknown>)._pollTimers = timers
    await poll()
  },

  cancelPolling: () => {
    const timers = (get() as Record<string, unknown>)._pollTimers as ReturnType<typeof setTimeout>[] | undefined
    if (timers) {
      timers.forEach(clearTimeout)
    }
  },

  fetchScanResults: async (scanId: string) => {
    try {
      const data = await unwrap<Record<string, unknown>>(
        fetch(`${API_BASE_URL}/api/v1/scanner/${scanId}/results`, { credentials: 'include' })
          .then(async (res) => { if (!res.ok) throw new Error('Failed to fetch results'); return res.json() })
      )

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
    })
  },

  clearError: () => set({ error: null }),
}))