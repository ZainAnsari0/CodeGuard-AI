import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { apiFetch } from '../lib/api'
import type { ScanResult, ScanHistoryItem, AiExplanationRequest, AiExplanationResult, FixSuggestion, Finding } from '../types'

export function useScanResults(scanId: string | undefined) {
  const { isAuthenticated } = useAuthStore()

  return useQuery<ScanResult>({
    queryKey: ['scan-results', scanId],
    queryFn: () => apiFetch<ScanResult>(`/api/v1/scanner/${scanId}/results`),
    enabled: !!scanId && isAuthenticated,
    staleTime: 30 * 1000,
  })
}

export function useScanHistory(skip = 0, limit = 20) {
  const { isAuthenticated } = useAuthStore()

  return useQuery<{ items: ScanHistoryItem[]; total: number }>({
    queryKey: ['scan-history', skip, limit],
    queryFn: async () => {
      const response = await apiFetch<any>(`/api/v1/analysis?skip=${skip}&limit=${limit}`)
      // Backend returns paginated envelope: { data: Analysis[], pagination: {...} }
      // Normalize to { items, total } expected by the UI
      if (Array.isArray(response)) {
        return { items: response as ScanHistoryItem[], total: response.length }
      }
      if (response && typeof response === 'object') {
        const items = response.data || response.items || []
        const total = response.pagination?.total ?? response.total ?? items.length
        return { items: items as ScanHistoryItem[], total }
      }
      return { items: [], total: 0 }
    },
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000,
  })
}

export function useAiExplanation() {
  return useMutation<AiExplanationResult, Error, AiExplanationRequest>({
    mutationFn: (request: AiExplanationRequest) =>
      apiFetch<AiExplanationResult>('/api/v1/ai/explain', {
        method: 'POST',
        body: JSON.stringify(request),
      }),
  })
}

export function usePreviewFix(scanId: string, findingId: string) {
  return useMutation<FixSuggestion, Error, void>({
    mutationFn: () =>
      apiFetch<FixSuggestion>(
        `/api/v1/scanner/${scanId}/findings/${findingId}/preview-fix`,
        { method: 'POST' }
      ),
  })
}

export function useApplyFix(scanId: string, findingId: string) {
  const queryClient = useQueryClient()

  return useMutation<{ finding_id: string; new_status: string }, Error, void>({
    mutationFn: () =>
      apiFetch<{ finding_id: string; new_status: string }>(
        `/api/v1/scanner/${scanId}/findings/${findingId}/apply-fix`,
        { method: 'POST' }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan-results', scanId] })
    },
  })
}

export function useEnrichFinding(scanId: string, findingId: string) {
  const queryClient = useQueryClient()

  return useMutation<Finding, Error, void>({
    mutationFn: () =>
      apiFetch<Finding>(
        `/api/v1/scanner/${scanId}/findings/${findingId}/enrich`,
        { method: 'POST' }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan-results', scanId] })
    },
  })
}