import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('saas-impacto-locale', 'pt-BR'));
});

test.describe('Module 6 — Municipality Selector', () => {
  test('page loads without crash', async ({ page }) => {
    await page.goto('/dashboard/module6');
    await page.waitForTimeout(2000);

    const errorOverlay = page.locator('vite-error-overlay');
    await expect(errorOverlay).toHaveCount(0);
  });

  test('route contains module6 in URL', async ({ page }) => {
    await page.goto('/dashboard/module6');
    expect(page.url()).toContain('/dashboard/module6');
  });

  test('sidebar has module6 link', async ({ page }) => {
    await page.goto('/dashboard/module6');
    await page.waitForSelector('nav', { timeout: 10_000 });

    const link = page.locator('nav a[href="/dashboard/module6"]');
    await expect(link).toBeVisible();
  });
});
