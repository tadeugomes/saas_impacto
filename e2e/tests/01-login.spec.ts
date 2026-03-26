/**
 * E2E — Login flow
 *
 * Cenários:
 * 1. Redirect para /login quando não autenticado
 * 2. Login com credenciais inválidas mostra erro
 * 3. Login com credenciais válidas redireciona para /dashboard
 * 4. Logout limpa sessão e redireciona para /login
 */

import { test, expect } from '@playwright/test';
import { TEST_USER } from '../fixtures/env';

// These tests run WITHOUT the saved auth state (they test the login page itself)
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Login', () => {
  test('redireciona para /login quando não autenticado', async ({ page }) => {
    await page.goto('/dashboard/module1');
    await expect(page).toHaveURL(/\/login/);
  });

  test('exibe erro com credenciais inválidas', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('E-mail').fill('naoexiste@test.com');
    await page.getByLabel('Senha').fill('senhaerrada');
    await page.getByRole('button', { name: /entrar/i }).click();

    // Error message must appear — exact text depends on API response
    const errorEl = page.locator('[class*="red"]').first();
    await expect(errorEl).toBeVisible({ timeout: 10_000 });
  });

  test('login válido redireciona para /dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('E-mail').fill(TEST_USER.email);
    await page.getByLabel('Senha').fill(TEST_USER.password);
    await page.getByRole('button', { name: /entrar/i }).click();

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 20_000 });
    await expect(page.getByRole('navigation')).toBeVisible();
  });
});
