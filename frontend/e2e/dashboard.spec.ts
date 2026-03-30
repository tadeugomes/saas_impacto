import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('saas-impacto-locale', 'pt-BR'));
});

test.describe('Dashboard Home', () => {
  test('page loads without crash', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // No Vite error overlay
    const errorOverlay = page.locator('vite-error-overlay');
    await expect(errorOverlay).toHaveCount(0);
  });

  test('navigation sidebar has module links', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('nav', { timeout: 10_000 });

    const navLinks = page.locator('nav a');
    const count = await navLinks.count();
    expect(count).toBeGreaterThanOrEqual(10);
  });

  test('sidebar has link to each module path', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('nav', { timeout: 10_000 });

    const paths = [
      '/dashboard/module1',
      '/dashboard/module5',
      '/dashboard/module7',
      '/dashboard/module11',
    ];

    for (const path of paths) {
      const link = page.locator(`nav a[href="${path}"]`);
      await expect(link).toBeVisible();
    }
  });

  test('app header is visible', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('header, [role="banner"]', { timeout: 10_000 });

    // App title in header
    const appTitle = page.getByText('SaaS Impacto Portuário');
    await expect(appTitle).toBeVisible();
  });
});
