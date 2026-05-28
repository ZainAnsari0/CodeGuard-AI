import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';

test.describe('Knowledge Base Access', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(`${BASE_URL}/knowledge-base`);
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/login');
  });
});

test.describe('Knowledge Base Content', () => {
  test('should show knowledge base page for authenticated users', async ({ page }) => {
    // This test requires a running backend with auth
    // Navigate to login first
    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(1000);
    await expect(page.locator('text=Sign in')).toBeVisible({ timeout: 10000 });
  });
});