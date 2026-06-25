import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useScanStore } from '../../store/scanStore'

describe('ScanPage (via ScanStore)', () => {
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

  it('starts with empty scan state', () => {
    const state = useScanStore.getState()
    expect(state.currentScanId).toBeNull()
    expect(state.scanStatus).toBeNull()
    expect(state.findings).toEqual([])
  })

  it('tracks upload state', async () => {
    globalThis.fetch = vi.fn().mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          scan_id: 'scan-test-1',
          file_count: 2,
          status: 'pending',
        }),
        { status: 200 }
      )
    )

    const file = new File(['content'], 'test.py', { type: 'text/x-python' })
    const result = await useScanStore.getState().uploadFiles([file], 'python')

    expect(result.success).toBe(true)
    expect(result.scanId).toBe('scan-test-1')
    expect(useScanStore.getState().currentScanId).toBe('scan-test-1')
    expect(useScanStore.getState().scanStatus).toBe('pending')
    expect(useScanStore.getState().totalFiles).toBe(2)
  })

  it('handles upload error gracefully', async () => {
    globalThis.fetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Invalid file type' }), { status: 400 })
    )

    const file = new File(['content'], 'test.exe', { type: 'application/octet-stream' })
    const result = await useScanStore.getState().uploadFiles([file], 'python')

    expect(result.success).toBe(false)
    expect(useScanStore.getState().error).toBe('Invalid file type')
  })

  it('handles network error during upload', async () => {
    globalThis.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'))

    const file = new File(['content'], 'test.py', { type: 'text/x-python' })
    const result = await useScanStore.getState().uploadFiles([file], 'python')

    expect(result.success).toBe(false)
    expect(useScanStore.getState().error).toBe('Network error')
  })

  it('fetches scan status', async () => {
    useScanStore.setState({ currentScanId: 'scan-1' })

    globalThis.fetch = vi.fn().mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: 'analyzing',
          progress: 50,
          stage: 'AI Analysis',
          total_files: 5,
        }),
        { status: 200 }
      )
    )

    await useScanStore.getState().fetchScanStatus('scan-1')

    expect(useScanStore.getState().scanStatus).toBe('analyzing')
    expect(useScanStore.getState().progress).toBe(50)
    expect(useScanStore.getState().stage).toBe('AI Analysis')
  })

  it('fetches scan results', async () => {
    useScanStore.setState({ currentScanId: 'scan-1' })

    const mockFindings = [
      { id: '1', vulnerability_type: 'XSS', severity: 'high', title: 'XSS Vulnerability', description: 'Test', analyzer_type: 'ai', cwe_id: 'CWE-79', cvss_score: null, file_path: 'test.py', line_start: 10, line_end: 12, code_snippet: null, status: 'open', confidence: 0.9, fix_suggestions: [] },
    ]

    globalThis.fetch = vi.fn().mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          findings: mockFindings,
          code_files: { 'test.py': 'print("hello")' },
          status: 'completed',
          total_files: 1,
        }),
        { status: 200 }
      )
    )

    await useScanStore.getState().fetchScanResults('scan-1')

    expect(useScanStore.getState().findings).toHaveLength(1)
    expect(useScanStore.getState().findings[0].vulnerability_type).toBe('XSS')
    expect(useScanStore.getState().scanStatus).toBe('completed')
  })

  it('clears scan state completely', () => {
    useScanStore.setState({
      currentScanId: 'scan-1',
      scanStatus: 'completed',
      progress: 100,
      findings: [{ id: '1' } as any],
      error: 'some error',
    })

    useScanStore.getState().clearScan()

    const state = useScanStore.getState()
    expect(state.currentScanId).toBeNull()
    expect(state.scanStatus).toBeNull()
    expect(state.progress).toBe(0)
    expect(state.findings).toEqual([])
    expect(state.error).toBeNull()
  })
})