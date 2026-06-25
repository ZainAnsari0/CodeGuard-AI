import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { unwrapPaginated } from '../lib/api'
import { RecentAnalysis } from '../types'

interface ProjectItem {
  id: string
  name: string
  description: string | null
  created_at: string | null
}

export function useDashboardData() {
  const { isAuthenticated } = useAuthStore()

  const projectsQuery = useQuery({
    queryKey: ['dashboard', 'projects'],
    queryFn: async () => {
      const res = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api/v1/projects?skip=0&limit=100`, { credentials: 'include' })
      if (!res.ok) throw new Error('Failed to fetch projects')
      return unwrapPaginated<{ items: ProjectItem[]; total: number }>(await res.json())
    },
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000,
  })

  const analysesQuery = useQuery({
    queryKey: ['dashboard', 'analyses'],
    queryFn: async () => {
      const res = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api/v1/analysis?skip=0&limit=10`, { credentials: 'include' })
      if (!res.ok) throw new Error('Failed to fetch analyses')
      return unwrapPaginated<{ items: RecentAnalysis[]; total: number }>(await res.json())
    },
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000,
  })

  const isLoading = projectsQuery.isLoading || analysesQuery.isLoading
  const error = projectsQuery.error || analysesQuery.error

  const totalProjects = (projectsQuery.data as { total?: number } | undefined)?.total ?? 0
  const recentAnalyses = ((analysesQuery.data as { items?: RecentAnalysis[] } | undefined)?.items ?? []) as RecentAnalysis[]

  // Compute code files, vulnerabilities, and security score from analysis data
  let totalCodeFiles = 0
  let totalVulnerabilities = 0
  let securityScore = 0

  if (recentAnalyses) {
    const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 }
    recentAnalyses.forEach((analysis) => {
      if (analysis.summary && analysis.summary.by_severity) {
        const sev = analysis.summary.by_severity
        severityCounts.critical += (sev.critical as number) || 0
        severityCounts.high += (sev.high as number) || 0
        severityCounts.medium += (sev.medium as number) || 0
        severityCounts.low += (sev.low as number) || 0
      }
      totalCodeFiles += (analysis.summary?.file_count as number) || 0
    })
    totalVulnerabilities = severityCounts.critical + severityCounts.high + severityCounts.medium + severityCounts.low
    const weightedPenalty = severityCounts.critical * 10 + severityCounts.high * 5 + severityCounts.medium * 2 + severityCounts.low * 0.5
    securityScore = Math.max(0, Math.round(100 - weightedPenalty))
  }

  return {
    isLoading,
    error,
    totalProjects,
    totalCodeFiles,
    totalVulnerabilities,
    securityScore,
    recentAnalyses,
    refetch: () => {
      projectsQuery.refetch()
      analysesQuery.refetch()
    },
  }
}