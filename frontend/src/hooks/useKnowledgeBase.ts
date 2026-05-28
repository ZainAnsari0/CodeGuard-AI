import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { apiFetch } from '../lib/api'
import type { KBArticle, KBArticleSummary } from '../types'

export function useKBArticles(category?: string, search?: string, page = 1) {
  const { isAuthenticated } = useAuthStore()
  const params = new URLSearchParams({ page: String(page), per_page: '20' })
  if (category) params.set('category', category)
  if (search) params.set('search', search)

  return useQuery<{ articles: KBArticleSummary[]; total: number }>({
    queryKey: ['kb-articles', category, search, page],
    queryFn: () => apiFetch(`/api/v1/kb/articles?${params.toString()}`),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  })
}

export function useKBArticle(slug: string | undefined) {
  const { isAuthenticated } = useAuthStore()
  return useQuery<KBArticle>({
    queryKey: ['kb-article', slug],
    queryFn: () => apiFetch(`/api/v1/kb/articles/${slug}`),
    enabled: !!slug && isAuthenticated,
    staleTime: 10 * 60 * 1000,
  })
}

export function useKBCategories() {
  const { isAuthenticated } = useAuthStore()
  return useQuery<string[]>({
    queryKey: ['kb-categories'],
    queryFn: () => apiFetch<string[]>('/api/v1/kb/categories'),
    enabled: isAuthenticated,
    staleTime: 30 * 60 * 1000,
  })
}

export function useKBSearch(query: string) {
  const { isAuthenticated } = useAuthStore()
  return useQuery<{ articles: KBArticleSummary[]; total: number }>({
    queryKey: ['kb-search', query],
    queryFn: () => apiFetch(`/api/v1/kb/search?q=${encodeURIComponent(query)}`),
    enabled: !!query && isAuthenticated,
    staleTime: 60 * 1000,
  })
}