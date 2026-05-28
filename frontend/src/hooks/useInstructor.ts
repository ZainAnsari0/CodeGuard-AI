import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { apiFetch } from '../lib/api'
import type { ClassInfo, Enrollment, ClassMetrics } from '../types'

export function useInstructorClasses() {
  const { isAuthenticated } = useAuthStore()
  return useQuery<ClassInfo[]>({
    queryKey: ['instructor-classes'],
    queryFn: () => apiFetch<ClassInfo[]>('/api/v1/instructor/classes'),
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateClass() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      apiFetch<ClassInfo>('/api/v1/instructor/classes', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instructor-classes'] })
    },
  })
}

export function useClassStudents(classId: string | undefined) {
  const { isAuthenticated } = useAuthStore()
  return useQuery<Enrollment[]>({
    queryKey: ['class-students', classId],
    queryFn: () => apiFetch<Enrollment[]>(`/api/v1/instructor/classes/${classId}/students`),
    enabled: !!classId && isAuthenticated,
  })
}

export function useEnrollInClass() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ classId, joinCode }: { classId: string; joinCode: string }) =>
      apiFetch<Enrollment>(`/api/v1/instructor/classes/${classId}/enroll`, {
        method: 'POST',
        body: JSON.stringify({ join_code: joinCode }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instructor-classes'] })
    },
  })
}

export function useClassMetrics(classId: string | undefined) {
  const { isAuthenticated } = useAuthStore()
  return useQuery<ClassMetrics>({
    queryKey: ['class-metrics', classId],
    queryFn: () => apiFetch<ClassMetrics>(`/api/v1/instructor/classes/${classId}/metrics`),
    enabled: !!classId && isAuthenticated,
    staleTime: 5 * 60 * 1000,
  })
}

export function useRemoveStudent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ classId, studentId }: { classId: string; studentId: string }) =>
      apiFetch(`/api/v1/instructor/classes/${classId}/students/${studentId}`, {
        method: 'DELETE',
      }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['class-students', variables.classId] })
    },
  })
}