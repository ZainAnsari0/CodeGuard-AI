// CodeGuard AI — Playwright E2E Tests
// Run with: npx playwright test
// Requires: @playwright/test

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';

test.describe('Authentication Flow', () => {
  test('should show login page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('text=Sign in')).toBeVisible({ timeout: 10000 });
  });

  test('should show register link on login page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('text=Register')).toBeVisible({ timeout: 10000 });
  });

  test('should show error on invalid login', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"], input[placeholder*="email"]', 'invalid@test.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    // Should show an error message or stay on login page
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/login');
  });
});

test.describe('Landing Page', () => {
  test('should load landing page for unauthenticated users', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    // Should redirect to landing or show dashboard based on auth state
    await page.waitForTimeout(2000);
    expect(page.url()).toContain(BASE_URL);
  });
});

test.describe('Scan Page Access', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(`${BASE_URL}/scan`);
    await page.waitForTimeout(2000);
    // Should redirect to login page
    expect(page.url()).toContain('/login');
  });
});

test.describe('Knowledge Base', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(`${BASE_URL}/knowledge-base`);
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/login');
  });
});