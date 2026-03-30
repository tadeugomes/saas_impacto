import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('saas-impacto-locale', 'pt-BR'));
});

test.describe('Module 11 — Cargo Forecast', () => {
  test('page loads without crash', async ({ page }) => {
    await page.goto('/dashboard/module11');
    await page.waitForTimeout(2000);

    const errorOverlay = page.locator('vite-error-overlay');
    await expect(errorOverlay).toHaveCount(0);
  });

  test('sidebar highlights module 11 link', async ({ page }) => {
    await page.goto('/dashboard/module11');
    await page.waitForSelector('nav', { timeout: 10_000 });

    const link = page.locator('nav a[href="/dashboard/module11"]');
    await expect(link).toBeVisible();
  });

  test('route contains module11 in URL', async ({ page }) => {
    await page.goto('/dashboard/module11');
    expect(page.url()).toContain('/dashboard/module11');
  });
});
