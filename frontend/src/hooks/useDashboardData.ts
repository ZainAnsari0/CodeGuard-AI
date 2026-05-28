import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { apiFetch } from '../lib/api'

interface ProjectItem {
  id: string
  name: string
  description: string | null
  created_at: string | null
}

interface AnalysisItem {
  id: string
  status: string
  branch: string
  created_at: string | null
  completed_at: string | null
  summary: Record<string, unknown> | null
}

export function useDashboardData() {
  const { isAuthenticated } = useAuthStore()

  const projectsQuery = useQuery({
    queryKey: ['dashboard', 'projects'],
    queryFn: () =>
      apiFetch<{ items: ProjectItem[]; total: number }>(
        '/api/v1/projects?skip=0&limit=100'
      ),
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000,
  })

  const analysesQuery = useQuery({
    queryKey: ['dashboard', 'analyses'],
    queryFn: () =>
      apiFetch<{ items: AnalysisItem[]; total: number }>(
        '/api/v1/analysis?skip=0&limit=10'
      ),
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000,
  })

  const isLoading = projectsQuery.isLoading || analysesQuery.isLoading
  const error = projectsQuery.error || analysesQuery.error

  const totalProjects = (projectsQuery.data as { total?: number } | undefined)?.total ?? 0
  const recentAnalyses = ((analysesQuery.data as { items?: AnalysisItem[] } | undefined)?.items ?? []) as AnalysisItem[]

  // Compute code files, vulnerabilities, and security score from analysis data
  let totalCodeFiles = 0
  let totalVulnerabilities = 0
  let securityScore = 0

  if (recentAnalyses) {
    const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 }
    recentAnalyses.forEach((analysis) => {
      if (analysis.summary && (analysis.summary as Record<string, unknown>).by_severity) {
        const sev = (analysis.summary as Record<string, Record<string, number>>).by_severity
        severityCounts.critical += sev.critical || 0
        severityCounts.high += sev.high || 0
        severityCounts.medium += sev.medium || 0
        severityCounts.low += sev.low || 0
      }
      totalCodeFiles += ((analysis.summary as Record<string, unknown>)?.file_count as number) || 0
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