export type Role = 'developer' | 'instructor' | 'admin'

export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'

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

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  loginAttempted: boolean
}

export interface AuthActions {
  setUser: (user: User) => void
  setError: (error: string | null) => void
  clearError: () => void
  setLoading: (isLoading: boolean) => void
  login: (email: string, password: string) => Promise<{ success: boolean; user?: User; error?: string }>
  register: (email: string, password: string, name: string, role?: string) => Promise<{ success: boolean; user?: User; error?: string }>
  logout: () => Promise<void>
  refreshAuthToken: () => Promise<{ success: boolean; token?: string; error?: string } | null>
  checkAuthStatus: () => Promise<boolean>
  forgotPassword: (email: string) => Promise<{ success: boolean; message?: string }>
  resetPassword: (token: string, newPassword: string) => Promise<{ success: boolean; message?: string; error?: string }>
  isDeveloper: () => boolean
  isInstructor: () => boolean
  isAdmin: () => boolean
  hasRole: (role: string) => boolean
}

export type AuthStore = AuthState & AuthActions

export interface FixSuggestion {
  id: string
  title: string
  description: string
  priority: number
  code_before: string | null
  code_after: string | null
  language: string
}

export interface Finding {
  id: string
  vulnerability_type: string
  severity: FindingSeverity
  title: string
  description: string | null
  analyzer_type: string
  cwe_id: string | null
  cvss_score: string | null
  file_path: string
  line_start: number | null
  line_end: number | null
  code_snippet: string | null
  status: string
  confidence: number | null
  fix_suggestions: FixSuggestion[]
}

export interface ScanResult {
  scan_id: string
  status: string
  total_files: number
  findings: Finding[]
  code_files: Record<string, string>
  summary: {
    total_findings: number
    by_severity: Record<string, number>
    by_type?: Record<string, number>
  } | null
}

export interface ScanHistoryItem {
  id: string
  project_id: string | null
  branch: string
  status: string
  started_at: string | null
  completed_at: string | null
  summary: ScanResult['summary'] | null
  created_at: string | null
}

export interface AiExplanationRequest {
  vulnerability_type: string
  severity: string
  cwe_id?: string | null
  file_path?: string | null
  code_snippet?: string | null
  language: string
}

export interface AiExplanationResult {
  title: string
  description: string
  impact: string
  exploitation: string
  remediation: string
  references: string[]
  provider_used?: string
}

export interface ApiResponse<T = unknown> {
  success: boolean
  message?: string
  data?: T
  error?: string | Record<string, unknown>
  detail?: string
  errors?: Array<{ message: string }>
}

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

export interface PlaceholderPageProps {
  title: string
  description: string
}

// --- Instructor / Class types ---

export interface ClassInfo {
  id: string
  name: string
  description: string | null
  instructor_id: string
  join_code: string
  is_active: boolean
  student_count: number
  created_at: string | null
  updated_at: string | null
}

export interface Enrollment {
  id: string
  class_id: string
  student_id: string
  status: string
  enrolled_at: string | null
  student_name: string | null
  student_email: string | null
}

export interface ClassMetrics {
  class_id: string
  class_name: string
  total_students: number
  total_scans: number
  total_findings: number
  findings_by_severity: Record<string, number>
  findings_by_type: Record<string, number>
  avg_findings_per_student: number
  top_vulnerability_types: Array<{ type: string; count: number }>
}

// --- Admin types ---

export interface AdminUser {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  last_login: string | null
  created_at: string | null
}

export interface ServiceStatus {
  name: string
  status: string
  latency_ms: number | null
  details: string | null
}

export interface SystemHealth {
  status: string
  uptime_seconds: number
  services: ServiceStatus[]
  version: string
}

export interface EventLog {
  id: string
  event_type: string
  severity: string
  user_id: string | null
  message: string
  metadata: Record<string, unknown> | null
  created_at: string | null
}

export interface TokenUsage {
  by_provider: Record<string, { total_calls: number; total_input_tokens: number; total_output_tokens: number; total_cost: number }>
  daily_totals: Record<string, { calls: number; input_tokens: number; output_tokens: number; cost: number }>
}

// --- Knowledge Base types ---

export interface KBArticle {
  id: string
  slug: string
  title: string
  category: string
  cwe_ids: string | null
  owasp_category: string | null
  content_markdown: string
  vulnerable_example: string | null
  safe_example: string | null
  is_published: boolean
  view_count: number
  created_at: string | null
  updated_at: string | null
}

export interface KBArticleSummary {
  id: string
  slug: string
  title: string
  category: string
  cwe_ids: string | null
  owasp_category: string | null
  is_published: boolean
  view_count: number
  created_at: string | null
}