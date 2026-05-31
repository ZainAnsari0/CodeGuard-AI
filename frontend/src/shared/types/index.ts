/**
 * Shared types used across multiple features.
 * Feature-specific types should live in their respective feature directories.
 */

// ─── API Response Envelope ─────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  success: boolean
  message?: string
  data?: T
  error?: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type PaginatedResponse<T> = ApiResponse<PaginatedData<T>>

// ─── Role & User ─────────────────────────────────────────────────────

export type Role = 'developer' | 'instructor' | 'admin'

export interface User {
  id: string
  email: string
  full_name: string | null
  role: Role
  is_active: boolean
  is_superuser: boolean
  last_login: string | null
  created_at: string | null
  updated_at: string | null
}

// ─── Severity ────────────────────────────────────────────────────────

export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'

// ─── Toast / UI ──────────────────────────────────────────────────────

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'
export type ModalName = 'search' | null

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
  duration?: number
}

// ─── Component Props ──────────────────────────────────────────────────

export interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: Role[]
}

export interface SidebarProps {
  isOpen: boolean
  toggleSidebar: () => void
}

export interface HeaderProps {
  toggleSidebar: () => void
}