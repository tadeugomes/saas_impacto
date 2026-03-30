import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('saas-impacto-locale', 'pt-BR'));
});

test.describe('Language Switching (i18n)', () => {
  test('defaults to Portuguese', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('h1', { timeout: 10_000 });

    // Language selector should show Português
    const langSelect = page.locator('select').filter({ hasText: 'Português' });
    await expect(langSelect).toBeVisible();
  });

  test('switches to English', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('h1', { timeout: 10_000 });

    // Find language selector and switch to English
    const langSelect = page.locator('select').filter({ hasText: 'Português' });
    await langSelect.selectOption('en-US');

    // Wait for re-render
    await page.waitForTimeout(500);

    // Sidebar should now show English labels
    await expect(page.locator('nav').getByText('Module 1')).toBeVisible();
  });

  test('language persists after navigation', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('nav', { timeout: 10_000 });

    // Switch to English
    const langSelect = page.locator('select').filter({ hasText: 'Português' });
    await langSelect.selectOption('en-US');
    await page.waitForTimeout(500);

    // Navigate to module 11
    await page.goto('/dashboard/module11');
    await page.waitForSelector('nav', { timeout: 10_000 });

    // Sidebar link should be in English
    const link = page.locator('nav a[href="/dashboard/module11"]');
    const text = await link.textContent();
    expect(text).toContain('Cargo');
  });

  test('switches back to Portuguese', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('h1', { timeout: 10_000 });

    // Switch to English first
    const langSelect = page.locator('select').filter({ hasText: 'Português' });
    await langSelect.selectOption('en-US');
    await page.waitForTimeout(500);

    // Switch back to Portuguese
    const langSelectEn = page.locator('select').filter({ hasText: 'English' });
    await langSelectEn.selectOption('pt-BR');
    await page.waitForTimeout(500);

    // Should be in Portuguese again
    await expect(page.locator('nav').getByText('Módulo 1')).toBeVisible();
  });
});
