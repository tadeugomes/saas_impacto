/**
 * E2E — Módulo 1: Eficiência Operacional
 *
 * Cenários:
 * 1. Login → seleção de instalação → visualização de indicador M1
 * 2. Filtro de ano atualiza dados exibidos
 * 3. Exportação (botão Export) está disponível
 */

import { test, expect } from '@playwright/test';
import { TEST_INSTALLATION_ID, TEST_YEAR } from '../fixtures/env';

test.describe('Módulo 1 — Eficiência Operacional', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/module1');
    await expect(page).toHaveURL(/dashboard\/module1/);
  });

  test('página carrega com título correto', async ({ page }) => {
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/efici/i);
  });

  test('seleciona instalação e exibe cards de indicadores', async ({ page }) => {
    // Look for installation selector (combobox or select)
    const installSelector = page
      .getByRole('combobox')
      .or(page.locator('select'))
      .first();

    await installSelector.selectOption({ value: TEST_INSTALLATION_ID });

    // Expect at least one indicator card to appear
    const cards = page.locator('[class*="card"], [class*="Card"]');
    await expect(cards.first()).toBeVisible({ timeout: 15_000 });
  });

  test('filtro de ano está acessível e mostra o ano atual', async ({ page }) => {
    const yearLabel = page.getByText(TEST_YEAR, { exact: true }).first();
    await expect(yearLabel).toBeVisible({ timeout: 8_000 });
  });

  test('botão de exportação está presente', async ({ page }) => {
    const exportBtn = page.getByRole('button', { name: /export|exportar/i });
    await expect(exportBtn).toBeVisible({ timeout: 8_000 });
  });
});
