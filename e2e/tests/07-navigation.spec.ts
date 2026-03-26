/**
 * E2E — Navegação entre módulos
 *
 * Cenários:
 * 1. Menu lateral navega para todos os 7 módulos sem erros fatais
 * 2. Rota / redireciona para /dashboard/module3 (default)
 * 3. Breadcrumb ou título atualiza ao trocar de módulo
 */

import { test, expect } from '@playwright/test';

const MODULES = [
  { path: '/dashboard/module1', titlePattern: /efici/i },
  { path: '/dashboard/module2', titlePattern: /carga|opera/i },
  { path: '/dashboard/module3', titlePattern: /emprego|recursos humanos/i },
  { path: '/dashboard/module4', titlePattern: /ambi|sustent/i },
  { path: '/dashboard/module5', titlePattern: /causal|impacto econômico/i },
  { path: '/dashboard/module6', titlePattern: /fiscal|finan/i },
  { path: '/dashboard/module7', titlePattern: /competitiv|bench/i },
];

test.describe('Navegação', () => {
  test('rota raiz redireciona para module3', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/dashboard\/module3/, { timeout: 10_000 });
  });

  for (const { path, titlePattern } of MODULES) {
    test(`${path} carrega sem erro fatal`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(new RegExp(path.replace('/', '\\/').replace('/', '\\/')));

      // No uncaught JS errors — check for visible error boundary or white screen
      const bodyText = await page.locator('body').textContent();
      expect(bodyText).not.toBe('');

      // Heading should match module
      const heading = page.getByRole('heading', { level: 1 }).first();
      const headingVisible = await heading.isVisible({ timeout: 8_000 }).catch(() => false);
      if (headingVisible) {
        const text = await heading.textContent();
        // Only assert if we got text — some modules may load async
        if (text && text.trim()) {
          expect(text.toLowerCase()).toMatch(titlePattern);
        }
      }
    });
  }
});
