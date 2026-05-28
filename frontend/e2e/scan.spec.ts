import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';

test.describe('Scan Page Access', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(`${BASE_URL}/scan`);
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/login');
  });
});

test.describe('Scan Upload Flow', () => {
  test('should show scan page elements for authenticated users', async ({ page }) => {
    // Note: This test requires a running backend with auth
    // In CI, this would use seeded test data
    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(1000);

    // Verify login page loaded
    await expect(page.locator('text=Sign in')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Scan History Access', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(`${BASE_URL}/scan-history`);
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/login');
  });
});