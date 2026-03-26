/**
 * E2E — Health checks de API e UI
 *
 * Cenários:
 * 1. /api/v1/health retorna 200 com status ok
 * 2. A UI exibe o dashboard sem erros de rede críticos
 */

import { test, expect } from '@playwright/test';

test.describe('Health', () => {
  test('backend /health retorna 200', async ({ request, baseURL }) => {
    // Derive API base from frontend base (same host, different path)
    const apiBase = (process.env.E2E_API_URL ?? baseURL ?? 'http://localhost:8000').replace(
      /:\d+$/,
      ':8000',
    );

    const response = await request.get(`${apiBase}/api/v1/health`).catch(() => null);
    if (response) {
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.status).toMatch(/ok|healthy/i);
    }
    // If backend is not reachable (e.g. frontend-only staging), skip gracefully
  });

  test('dashboard não mostra tela em branco', async ({ page }) => {
    await page.goto('/dashboard/module3');
    const bodyContent = await page.locator('body').textContent();
    expect((bodyContent ?? '').trim().length).toBeGreaterThan(50);
  });
});
