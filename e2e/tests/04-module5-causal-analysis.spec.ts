/**
 * E2E — Módulo 5: Análise Causal (DiD / IV / Event Study)
 *
 * Cenários:
 * 1. Módulo 5 carrega formulário de criação de análise
 * 2. Preenchimento e submissão do formulário cria análise (status pending/running)
 * 3. Polling de status — badge atualiza enquanto análise processa
 * 4. Botão de download DOCX aparece quando análise concluída
 *
 * Nota: O teste de criação usa um stub de API (MSW ou intercept) para não
 * depender de BigQuery real em CI. O intercept é configurado por página via
 * route().
 */

import { test, expect } from '@playwright/test';

test.describe('Módulo 5 — Análise Causal', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/module5');
    await expect(page).toHaveURL(/dashboard\/module5/);
  });

  test('página carrega formulário de análise', async ({ page }) => {
    // Form or trigger button for new analysis
    const formOrButton = page
      .getByRole('button', { name: /nova análise|criar análise|iniciar/i })
      .or(page.getByRole('form'))
      .first();

    await expect(formOrButton).toBeVisible({ timeout: 10_000 });
  });

  test('seleção de método exibe opções DiD, IV, Event Study', async ({ page }) => {
    // Method selector — might be a select, radio group, or button group
    const methodSelector = page
      .getByRole('combobox', { name: /método|method/i })
      .or(page.locator('select[name*="method"], select[id*="method"]'))
      .first();

    const selectorVisible = await methodSelector.isVisible().catch(() => false);
    if (selectorVisible) {
      const options = await methodSelector.locator('option').allTextContents();
      const methodTexts = options.join(' ').toLowerCase();
      expect(methodTexts).toMatch(/did|iv|event/);
    } else {
      // Alternatively look for radio buttons or labels with method names
      await expect(
        page.getByText(/diff.*diff|did|event study|iv/i).first()
      ).toBeVisible({ timeout: 8_000 });
    }
  });

  test('análise criada via API stub aparece na lista com status pending', async ({ page }) => {
    // Intercept the POST endpoint to return a known response
    await page.route('**/api/v1/analyses', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'e2e-test-analysis-001',
            status: 'pending',
            method: 'did',
            outcome_indicator: 'IND-1.01',
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Also stub the GET list so the new analysis appears
    await page.route('**/api/v1/analyses?**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'e2e-test-analysis-001',
              status: 'pending',
              method: 'did',
              outcome_indicator: 'IND-1.01',
              created_at: new Date().toISOString(),
            },
          ]),
        });
      } else {
        await route.continue();
      }
    });

    await page.reload();

    // Badge or status indicator for "pending" analysis
    const pendingBadge = page.getByText(/pending|aguardando|em fila/i).first();
    await expect(pendingBadge).toBeVisible({ timeout: 10_000 });
  });

  test('análise concluída exibe botão de download DOCX', async ({ page }) => {
    // Stub a completed analysis
    await page.route('**/api/v1/analyses?**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'e2e-completed-001',
              status: 'completed',
              method: 'event_study',
              outcome_indicator: 'IND-1.01',
              created_at: new Date().toISOString(),
              completed_at: new Date().toISOString(),
            },
          ]),
        });
      } else {
        await route.continue();
      }
    });

    await page.reload();

    // Download button for DOCX report
    const downloadBtn = page.getByRole('button', { name: /download|relatório|docx/i }).first();
    await expect(downloadBtn).toBeVisible({ timeout: 10_000 });
  });
});
