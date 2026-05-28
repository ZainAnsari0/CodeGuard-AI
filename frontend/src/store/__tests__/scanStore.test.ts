import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useScanStore } from '../scanStore'

describe('ScanStore', () => {
  beforeEach(() => {
    useScanStore.setState({
      currentScanId: null,
      scanStatus: null,
      progress: 0,
      stage: null,
      totalFiles: 0,
      filesScanned: 0,
      findings: [],
      codeFiles: {},
      isUploading: false,
      error: null,
    })
  })

  it('initializes with default values', () => {
    const state = useScanStore.getState()
    expect(state.currentScanId).toBeNull()
    expect(state.scanStatus).toBeNull()
    expect(state.progress).toBe(0)
    expect(state.findings).toEqual([])
    expect(state.isUploading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('clears scan state', () => {
    useScanStore.setState({
      currentScanId: 'scan-123',
      scanStatus: 'completed',
      progress: 100,
      findings: [{ id: '1', vulnerability_type: 'XSS', severity: 'high' as const }],
    })

    useScanStore.getState().clearScan()

    const state = useScanStore.getState()
    expect(state.currentScanId).toBeNull()
    expect(state.scanStatus).toBeNull()
    expect(state.progress).toBe(0)
    expect(state.findings).toEqual([])
  })

  it('clears error', () => {
    useScanStore.setState({ error: 'Something went wrong' })
    useScanStore.getState().clearError()
    expect(useScanStore.getState().error).toBeNull()
  })

  it('handles upload success', async () => {
    globalThis.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        scan_id: 'scan-456',
        file_count: 3,
        status: 'pending',
      }),
    })

    // Set a token in auth store mock - scanStore reads token from store cast
    useScanStore.setState({ isUploading: false, error: null } as any)

    const file = new File(['test.py'], 'test.py', { type: 'text/x-python' })
    const result = await useScanStore.getState().uploadFiles([file], 'python')

    expect(useScanStore.getState().isUploading).toBe(false)
    expect(result.success).toBe(true)
  })

  it('handles upload failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: 'Upload failed' }),
    })

    const file = new File(['test.py'], 'test.py', { type: 'text/x-python' })
    const result = await useScanStore.getState().uploadFiles([file], 'python')

    expect(result.success).toBe(false)
    expect(useScanStore.getState().error).toBe('Upload failed')
  })

  it('sets uploading state during upload', async () => {
    let resolvePromise: (value: unknown) => void
    const pendingPromise = new Promise((resolve) => { resolvePromise = resolve })

    globalThis.fetch = vi.fn().mockReturnValueOnce(pendingPromise)

    const file = new File(['test.py'], 'test.py', { type: 'text/x-python' })
    const uploadPromise = useScanStore.getState().uploadFiles([file], 'python')

    // Should be uploading
    expect(useScanStore.getState().isUploading).toBe(true)

    // Resolve the fetch
    resolvePromise!({
      ok: true,
      json: () => Promise.resolve({ scan_id: 'scan-789', file_count: 1, status: 'pending' }),
    })

    await uploadPromise
    expect(useScanStore.getState().isUploading).toBe(false)
  })
})