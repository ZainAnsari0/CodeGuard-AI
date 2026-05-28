// CodeGuard AI — E2E Test Data Fixtures
// Shared test credentials and helpers for Playwright E2E tests

export const TEST_CREDENTIALS = {
  developer: {
    email: 'test-developer@codeguard.test',
    password: 'TestDev!Pass1',
    role: 'developer' as const,
  },
  instructor: {
    email: 'test-instructor@codeguard.test',
    password: 'TestInst!Pass1',
    role: 'instructor' as const,
  },
  admin: {
    email: 'test-admin@codeguard.test',
    password: 'TestAdmin!Pass1',
    role: 'admin' as const,
  },
}

export const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'
export const API_URL = process.env.E2E_API_URL || 'http://localhost:8000'

// Helper: Register a test user via API
export async function registerTestUser(
  request: import('@playwright/test').APIRequestContext,
  user: { email: string; password: string; role: string; fullName?: string }
) {
  const response = await request.post(`${API_URL}/api/v1/auth/register`, {
    data: {
      email: user.email,
      password: user.password,
      full_name: user.fullName || `Test ${user.role}`,
      role: user.role,
    },
  })
  return response
}

// Helper: Login and get auth token
export async function loginTestUser(
  request: import('@playwright/test').APIRequestContext,
  email: string,
  password: string
) {
  const response = await request.post(`${API_URL}/api/v1/auth/login`, {
    form: { username: email, password },
  })
  const data = await response.json()
  return data?.data?.access_token || data?.access_token || null
}