/**
 * Authentication setup — runs once before all E2E tests.
 * Logs in with test credentials and persists the browser storage state
 * to e2e/.auth/user.json so subsequent tests skip the login page.
 */

import { test as setup, expect } from '@playwright/test';
import { TEST_USER } from '../fixtures/env';

const AUTH_FILE = 'e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('E-mail').fill(TEST_USER.email);
  await page.getByLabel('Senha').fill(TEST_USER.password);
  await page.getByRole('button', { name: /entrar/i }).click();

  // Wait for redirect to dashboard after successful login
  await page.waitForURL(/\/dashboard/, { timeout: 20_000 });

  // Confirm the main navigation is visible — proof of authenticated state
  await expect(page.getByRole('navigation')).toBeVisible();

  await page.context().storageState({ path: AUTH_FILE });
});
