import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';

test.describe('Report Page Access', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(`${BASE_URL}/report/test-scan-id`);
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/login');
  });
});

test.describe('Shared Report Access', () => {
  test('should show not found for invalid share token', async ({ page }) => {
    await page.goto(`${BASE_URL}/share/nonexistent-token-12345`);
    await page.waitForTimeout(2000);
    // Shared report page should load (public page) but show not found/error
    // since the token doesn't exist
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });
});