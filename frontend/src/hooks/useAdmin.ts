import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { apiFetch } from '../lib/api'
import type { AdminUser, SystemHealth, EventLog, TokenUsage } from '../types'

export function useAdminUsers(page = 1, perPage = 20, role?: string, search?: string) {
  const { isAuthenticated } = useAuthStore()
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
  if (role) params.set('role', role)
  if (search) params.set('search', search)

  return useQuery<{ users: AdminUser[]; total: number; page: number; per_page: number }>({
    queryKey: ['admin-users', page, perPage, role, search],
    queryFn: () => apiFetch(`/api/v1/admin/users?${params.toString()}`),
    enabled: isAuthenticated,
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: { role?: string; is_active?: boolean; full_name?: string } }) =>
      apiFetch<AdminUser>(`/api/v1/admin/users/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
  })
}

export function useDeactivateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) =>
      apiFetch(`/api/v1/admin/users/${userId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
  })
}

export function useSystemHealth() {
  const { isAuthenticated } = useAuthStore()
  return useQuery<SystemHealth & { stats?: { total_users: number; total_scans: number } }>({
    queryKey: ['system-health'],
    queryFn: () => apiFetch('/api/v1/admin/system/health'),
    enabled: isAuthenticated,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  })
}

export function useEventLogs(page = 1, perPage = 50, eventType?: string, severity?: string) {
  const { isAuthenticated } = useAuthStore()
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
  if (eventType) params.set('event_type', eventType)
  if (severity) params.set('severity', severity)

  return useQuery<{ events: EventLog[]; total: number }>({
    queryKey: ['event-logs', page, perPage, eventType, severity],
    queryFn: () => apiFetch(`/api/v1/admin/system/events?${params.toString()}`),
    enabled: isAuthenticated,
  })
}

export function useTokenUsage() {
  const { isAuthenticated } = useAuthStore()
  return useQuery<{ token_usage: TokenUsage; provider_status: Record<string, boolean> }>({
    queryKey: ['token-usage'],
    queryFn: () => apiFetch('/api/v1/admin/system/token-usage'),
    enabled: isAuthenticated,
    staleTime: 60 * 1000,
  })
}