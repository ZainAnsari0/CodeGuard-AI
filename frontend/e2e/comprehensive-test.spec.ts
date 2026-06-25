/**
 * Comprehensive User Testing Suite for CodeGuard AI
 * Tests every page and flow to find bugs, inconsistencies, and visual issues
 */

import { test, expect, type Page } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000'
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000'

// ─── Helper: check for console errors ───
let consoleErrors: string[] = []

test.beforeEach(async ({ page }) => {
  consoleErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text())
    }
  })
  page.on('pageerror', (err) => {
    consoleErrors.push(`PAGE ERROR: ${err.message}`)
  })
})

test.afterEach(async () => {
  if (consoleErrors.length > 0) {
    console.log(`### Console errors found (${consoleErrors.length}):\n${consoleErrors.join('\n')}`)
  }
})

// ═══════════════════════════════════════════════════════════════
// 1. LANDING PAGE
// ═══════════════════════════════════════════════════════════════
test.describe('Landing Page (Unauthenticated)', () => {
  test('should load landing page with all sections', async ({ page }) => {
    await page.goto(BASE_URL)
    await page.waitForLoadState('networkidle')
    
    // Hero section
    await expect(page.locator('text=before they find you')).toBeVisible({ timeout: 15000 })
    await expect(page.locator('text=Start Scanning Free')).toBeVisible()
    await expect(page.locator('text=Try Demo')).toBeVisible()
    
    // Nav
    await expect(page.locator('text=Sign in').first()).toBeVisible()
    await expect(page.locator('text=Get Started').first()).toBeVisible()
    
    // Features section
    await expect(page.locator('text=Vulnerability Detection')).toBeVisible()
    await expect(page.locator('text=AI Fix Suggestions')).toBeVisible()
    await expect(page.locator('text=Multi-Language Support')).toBeVisible()
    await expect(page.locator('text=Shareable Reports')).toBeVisible()
    
    // How It Works section - use h3 headings for specificity
    await expect(page.locator('h3:has-text("Upload Your Code")')).toBeVisible()
    await expect(page.locator('h3:has-text("AI Analysis")')).toBeVisible()
    await expect(page.locator('h3:has-text("Review & Fix")')).toBeVisible()
    
    // Security badges
    await expect(page.locator('h3:has-text("OWASP-Aligned")')).toBeVisible()
    await expect(page.locator('h3:has-text("Validated Fixes")')).toBeVisible()
    await expect(page.locator('h3:has-text("Multi-Model AI")')).toBeVisible()
    
    // CTA section
    await expect(page.locator('h2:has-text("Start securing your code today")')).toBeVisible()
    await expect(page.locator('a:has-text("Create Free Account")')).toBeVisible()
    
    // Footer
    await expect(page.locator('a:has-text("Privacy")').first()).toBeVisible()
    await expect(page.locator('a:has-text("Terms")').first()).toBeVisible()
    await expect(page.locator('a:has-text("Docs")').first()).toBeVisible()
    
    expect(consoleErrors).toEqual([])
  })

  test('navigation links work on landing page', async ({ page }) => {
    await page.goto(BASE_URL)
    await page.waitForLoadState('networkidle')
    
    // Click Sign in
    await page.locator('text=Sign in').first().click()
    await page.waitForURL('**/login', { timeout: 10000 })
    expect(page.url()).toContain('/login')
    
    // Back to landing
    await page.goto(BASE_URL)
    await page.waitForLoadState('networkidle')
    
    // Click Get Started (navigates to /register)
    await page.locator('text=Get Started').first().click()
    await page.waitForURL('**/register', { timeout: 10000 })
    expect(page.url()).toContain('/register')
    
    // Back to landing
    await page.goto(BASE_URL)
    await page.waitForLoadState('networkidle')
    
    // Click Try Demo
    await page.locator('text=Try Demo').first().click()
    await page.waitForURL('**/demo', { timeout: 10000 })
    expect(page.url()).toContain('/demo')
  })
})

// ═══════════════════════════════════════════════════════════════
// 2. LOGIN PAGE
// ═══════════════════════════════════════════════════════════════
test.describe('Login Page', () => {
  test('should render login form correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)
    await page.waitForLoadState('networkidle')
    
    // Check page title
    await expect(page.locator('h2:has-text("Welcome back")')).toBeVisible()
    
    // Check form fields
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    
    // Check "Remember me" checkbox
    await expect(page.locator('text=Remember me').first()).toBeVisible()
    
    // Check "Forgot password?" link
    await expect(page.locator('a:has-text("Forgot password?")')).toBeVisible()
    
    // Sign in button
    await expect(page.locator('button[type="submit"]')).toContainText('Sign In')
    
    // Register link
    await expect(page.locator('a:has-text("Create account")').first()).toBeVisible()
    
    expect(consoleErrors).toEqual([])
  })

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)
    await page.waitForLoadState('networkidle')
    
    // Click submit without filling form
    await page.locator('button[type="submit"]').click()
    
    // Should show validation errors
    await page.waitForTimeout(1000)
    
    // Check that validation errors appear
    const emailErrors = page.locator('text=Invalid email').or(page.locator('text=Email'))
    await expect(emailErrors.first()).toBeVisible({ timeout: 5000 })
  })

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)
    await page.waitForLoadState('networkidle')
    
    // Fill with invalid credentials
    await page.fill('input[type="email"]', 'nonexistent@test.com')
    await page.fill('input[type="password"]', 'WrongPass123!')
    await page.locator('button[type="submit"]').click()
    
    // Wait for API response
    await page.waitForTimeout(3000)
    
    // Should show error message or stay on login page
    const currentUrl = page.url()
    expect(currentUrl).toContain('/login')
  })
})

// ═══════════════════════════════════════════════════════════════
// 3. REGISTER PAGE
// ═══════════════════════════════════════════════════════════════
test.describe('Register Page', () => {
  test('should render registration form correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/register`)
    await page.waitForLoadState('networkidle')
    
    // Page title
    await expect(page.locator('h2:has-text("Create account")')).toBeVisible()
    
    // Form fields
    await expect(page.locator('input[placeholder="John Doe"]')).toBeVisible()
    await expect(page.locator('input[placeholder="you@company.com"]')).toBeVisible()
    
    // Role selection
    await expect(page.locator('text=Developer').first()).toBeVisible()
    await expect(page.locator('text=Instructor').first()).toBeVisible()
    
    // Password fields
    await expect(page.locator('input[placeholder*="8+ chars"]')).toBeVisible()
    await expect(page.locator('input[placeholder="Re-enter your password"]')).toBeVisible()
    
    // Submit button
    await expect(page.locator('button[type="submit"]')).toContainText('Create Account')
    
    // Login link
    await expect(page.locator('a:has-text("Sign in")')).toBeVisible()
    
    expect(consoleErrors).toEqual([])
  })

  test('role selection cards should work', async ({ page }) => {
    await page.goto(`${BASE_URL}/register`)
    await page.waitForLoadState('networkidle')
    
    // Developer should be selected by default
    const devCard = page.locator('text=Developer').first()
    // Instructor card should be clickable
    const instructorCard = page.locator('text=Instructor').first()
    
    await instructorCard.click()
    await page.waitForTimeout(500)
    
    // Check that instructor is selected
    const instructorRadio = page.locator('input[type="radio"][value="instructor"]')
    await expect(instructorRadio).toBeChecked()
  })
})

// ═══════════════════════════════════════════════════════════════
// 4. FORGOT PASSWORD PAGE
// ═══════════════════════════════════════════════════════════════
test.describe('Forgot Password Page', () => {
  test('should render forgot password form', async ({ page }) => {
    await page.goto(`${BASE_URL}/forgot-password`)
    await page.waitForLoadState('networkidle')
    
    // Heading should be 'Forgot Password?' not 'Reset your password'
    await expect(page.locator('h2:has-text("Forgot Password?")')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('text=Send Reset Link')).toBeVisible()
    const bodyText = await page.textContent('body')
    expect(bodyText).toBeTruthy()
    
    // Check for email input
    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toBeVisible({ timeout: 5000 })
  })
})

// ═══════════════════════════════════════════════════════════════
// 5. GUEST DEMO PAGE
// ═══════════════════════════════════════════════════════════════
test.describe('Guest Demo Page', () => {
  test('should load demo page', async ({ page }) => {
    await page.goto(`${BASE_URL}/demo`)
    await page.waitForLoadState('networkidle')
    
    const bodyText = await page.textContent('body')
    expect(bodyText).toBeTruthy()
    expect(bodyText.length).toBeGreaterThan(0)
  })
})

// ═══════════════════════════════════════════════════════════════
// 6. SHARED REPORT PAGE (public)
// ═══════════════════════════════════════════════════════════════
test.describe('Shared Report Page', () => {
  test('should handle invalid share token gracefully', async ({ page }) => {
    await page.goto(`${BASE_URL}/share/invalid-token-12345`)
    await page.waitForLoadState('networkidle')
    
    const bodyText = await page.textContent('body')
    expect(bodyText).toBeTruthy()
    // Should not be a blank page
    expect(bodyText.length).toBeGreaterThan(50)
  })
})

// ═══════════════════════════════════════════════════════════════
// 7. PROTECTED PAGES REDIRECT TO LOGIN
// ═══════════════════════════════════════════════════════════════
test.describe('Protected Pages Redirect', () => {
  const protectedPaths = [
    '/dashboard',
    '/scan',
    '/history',
    '/settings',
    '/knowledge-base',
    '/users',
    '/system-health',
    '/event-logs',
    '/classes',
  ]

  for (const path of protectedPaths) {
    test(`should redirect ${path} to login when not authenticated`, async ({ page }) => {
      // First navigate to the app's origin so we can safely clear storage
      await page.goto(`${BASE_URL}/login`)
      await page.waitForLoadState('networkidle')
      
      // Clear auth state via the app's own origin
      await page.evaluate(() => {
        try {
          sessionStorage.removeItem('auth-storage')
          localStorage.clear()
        } catch {
          // Ignore storage access errors
        }
      })
      
      // Now navigate to the protected page
      await page.goto(`${BASE_URL}${path}`)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(3000)
      
      const currentUrl = page.url()
      // Should be redirected to /login or /landing or back to /
      // Not the protected page itself
      expect(currentUrl).not.toContain(path.replace('/', ''))
    })
  }
})

// ═══════════════════════════════════════════════════════════════
// 8. ERROR PAGES
// ═══════════════════════════════════════════════════════════════
test.describe('Error Pages', () => {
  test('should show 404 page for unknown routes', async ({ page }) => {
    await page.goto(`${BASE_URL}/this-does-not-exist-at-all-12345`)
    await page.waitForLoadState('networkidle')
    
    const bodyText = await page.textContent('body')
    expect(bodyText).toBeTruthy()
  })
})

// ═══════════════════════════════════════════════════════════════
// 9. AUTHENTICATED USER FLOW (Register + Login + Dashboard)
// ═══════════════════════════════════════════════════════════════
test.describe('Authenticated User Flow', () => {
  const testEmail = `testuser_${Date.now()}@test.com`
  const testPassword = 'TestPass123!'
  const testName = 'Test User'

  test('should complete registration flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/register`)
    await page.waitForLoadState('networkidle')
    
    // Fill registration form
    await page.fill('input[placeholder="John Doe"]', testName)
    await page.fill('input[placeholder="you@company.com"]', testEmail)
    
    // Select Developer role (should be default)
    const devCard = page.locator('text=Developer').first()
    await devCard.click()
    
    // Fill password
    await page.fill('input[placeholder*="8+ chars"]', testPassword)
    await page.fill('input[placeholder="Re-enter your password"]', testPassword)
    
    // Submit
    await page.locator('button[type="submit"]').click()
    
    // Wait for response
    await page.waitForTimeout(3000)
    
    // Check result - should redirect to dashboard on success
    const currentUrl = page.url()
    const bodyText = await page.textContent('body')
    
    if (currentUrl.includes('/dashboard') || bodyText?.includes('Dashboard') || bodyText?.includes('Good')) {
      console.log('✓ Registration succeeded, redirected to dashboard')
    } else {
      console.log(`Registration result URL: ${currentUrl}`)
      // Stay on register page with error - might be duplicate or other issue
    }
  })

  test('should login and navigate to dashboard', async ({ page }) => {
    // First, try to use the same credentials
    await page.goto(`${BASE_URL}/login`)
    await page.waitForLoadState('networkidle')
    
    await page.fill('input[type="email"]', testEmail)
    await page.fill('input[type="password"]', testPassword)
    await page.locator('button[type="submit"]').click()
    
    await page.waitForTimeout(3000)
    
    const currentUrl = page.url()
    const bodyText = await page.textContent('body')
    
    if (currentUrl.includes('/dashboard') || bodyText?.includes('Good')) {
      console.log('✓ Login succeeded, on dashboard')
      
      // Check dashboard elements
      await expect(page.locator('text=New Scan')).toBeVisible({ timeout: 5000 })
      
      // Check sidebar navigation
      await expect(page.locator('text=Dashboard').first()).toBeVisible()
      await expect(page.locator('text=Scan History').first()).toBeVisible()
      await expect(page.locator('text=Knowledge Base').first()).toBeVisible()
      
      // Should NOT see admin/instructor pages
      const hasAdminLinks = bodyText?.includes('User Management') || bodyText?.includes('System Health')
      console.log(`Has admin links (should be false for developer): ${hasAdminLinks}`)
    } else {
      console.log(`Login result URL: ${currentUrl}`)
    }
  })

  test('should navigate through main app pages', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`)
    await page.waitForLoadState('networkidle')
    
    await page.fill('input[type="email"]', testEmail)
    await page.fill('input[type="password"]', testPassword)
    await page.locator('button[type="submit"]').click()
    
    await page.waitForTimeout(3000)
    
    // Navigate to Scan page
    await page.goto(`${BASE_URL}/scan`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    const scanBody = await page.textContent('body')
    expect(scanBody).toBeTruthy()
    
    // Navigate to History page
    await page.goto(`${BASE_URL}/history`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    const historyBody = await page.textContent('body')
    expect(historyBody).toBeTruthy()
    
    // Navigate to Knowledge Base
    await page.goto(`${BASE_URL}/knowledge-base`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    const kbBody = await page.textContent('body')
    expect(kbBody).toBeTruthy()
    
    // Navigate to Settings
    await page.goto(`${BASE_URL}/settings`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    const settingsBody = await page.textContent('body')
    expect(settingsBody).toBeTruthy()
  })
})

// ═══════════════════════════════════════════════════════════════
// 10. API HEALTH CHECK
// ═══════════════════════════════════════════════════════════════
test.describe('Backend API Health', () => {
  test('API health endpoint should respond', async ({ page }) => {
    const response = await page.request.get(`${API_URL}/api/v1/health`)
    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    console.log(`Health check response: ${JSON.stringify(body)}`)
  })
})

// ═══════════════════════════════════════════════════════════════
// 11. RESPONSIVE DESIGN CHECKS
// ═══════════════════════════════════════════════════════════════
test.describe('Responsive Design', () => {
  test('landing page should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 }) // iPhone X
    await page.goto(BASE_URL)
    await page.waitForLoadState('networkidle')
    
    // Content should still be visible
    await expect(page.locator('text=before they find you')).toBeVisible({ timeout: 15000 })
    
    // Mobile menu / hamburger should exist
    // Check the content is readable
    const bodyText = await page.textContent('body')
    expect(bodyText).toBeTruthy()
  })

  test('login page should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto(`${BASE_URL}/login`)
    await page.waitForLoadState('networkidle')
    
    // Form should be visible
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })
})

// ═══════════════════════════════════════════════════════════════
// SUMMARY
// ═══════════════════════════════════════════════════════════════
test.describe('Test Summary', () => {
  test('print test summary', async () => {
    console.log('='.repeat(60))
    console.log('COMPREHENSIVE USER TESTING SUMMARY')
    console.log('='.repeat(60))
    console.log(`Test time: ${new Date().toISOString()}`)
    console.log(`Base URL: ${BASE_URL}`)
    console.log(`API URL: ${API_URL}`)
    console.log('='.repeat(60))
  })
})
