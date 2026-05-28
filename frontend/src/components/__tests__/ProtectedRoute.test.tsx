import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { renderWithProviders } from '../../test/utils'
import { useAuthStore } from '../../store/authStore'
import { ProtectedRoute } from '../auth/ProtectedRoute'

// Mock the lucide-react icon to avoid SVG rendering issues
vi.mock('lucide-react', () => ({
  Shield: () => <svg data-testid="shield-icon" />,
}))

function TestChild() {
  return <div data-testid="protected-content">Protected Content</div>
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      loginAttempted: false,
    })
  })

  it('redirects to login when not authenticated', () => {
    renderWithProviders(
      <ProtectedRoute>
        <TestChild />
      </ProtectedRoute>,
    )
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('shows loading state when isLoading is true', () => {
    useAuthStore.setState({ isLoading: true })
    renderWithProviders(
      <ProtectedRoute>
        <TestChild />
      </ProtectedRoute>,
    )
    // Loading state shows "Authenticating" text
    expect(screen.getByText('Authenticating')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated with no role restriction', () => {
    useAuthStore.setState({
      user: { id: '1', email: 'dev@test.com', role: 'developer', is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null },
      isAuthenticated: true,
      isLoading: false,
    })

    renderWithProviders(
      <ProtectedRoute>
        <TestChild />
      </ProtectedRoute>,
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('renders children when role matches allowedRoles', () => {
    useAuthStore.setState({
      user: { id: '1', email: 'admin@test.com', role: 'admin', is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null },
      isAuthenticated: true,
      isLoading: false,
    })

    renderWithProviders(
      <ProtectedRoute allowedRoles={['admin']}>
        <TestChild />
      </ProtectedRoute>,
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('redirects when role does not match allowedRoles', () => {
    useAuthStore.setState({
      user: { id: '1', email: 'dev@test.com', role: 'developer', is_active: true, full_name: null, name: null, is_superuser: false, last_login: null, created_at: null, updated_at: null },
      isAuthenticated: true,
      isLoading: false,
    })

    renderWithProviders(
      <ProtectedRoute allowedRoles={['admin']}>
        <TestChild />
      </ProtectedRoute>,
    )

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })
})