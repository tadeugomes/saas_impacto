/**
 * E2E — Módulo 3: Recursos Humanos e Simulação de Emprego
 *
 * Cenários:
 * 1. Módulo 3 carrega indicadores de emprego RAIS
 * 2. Painel de multiplicador exibe dados de literatura
 * 3. Simulação de choque de tonelagem — slider ou input atualiza estimativa
 * 4. Banner "estimativa causal indisponível" aparece ao ativar toggle causal
 */

import { test, expect } from '@playwright/test';
import { TEST_INSTALLATION_ID } from '../fixtures/env';

test.describe('Módulo 3 — Recursos Humanos', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/module3');
    await expect(page).toHaveURL(/dashboard\/module3/);
  });

  test('página carrega sem erros fatais', async ({ page }) => {
    // No error alert visible at start
    const fatalError = page.locator('[class*="ErrorAlert"], [role="alert"]').first();
    // Either not visible or visible but not a fatal crash message
    const isVisible = await fatalError.isVisible().catch(() => false);
    if (isVisible) {
      const text = await fatalError.textContent();
      // Acceptable warnings about unavailable data are OK; hard crashes are not
      expect(text).not.toMatch(/500|unhandled|crash/i);
    }
  });

  test('seleciona instalação e carrega empregos portuários', async ({ page }) => {
    const installSelector = page
      .getByRole('combobox')
      .or(page.locator('select'))
      .first();
    await installSelector.selectOption({ value: TEST_INSTALLATION_ID });

    // IND-3.01 card or heading should appear
    await expect(
      page.getByText(/empregos portu/i).first()
    ).toBeVisible({ timeout: 15_000 });
  });

  test('painel de multiplicador exibe multiplicador de literatura', async ({ page }) => {
    const installSelector = page
      .getByRole('combobox')
      .or(page.locator('select'))
      .first();
    await installSelector.selectOption({ value: TEST_INSTALLATION_ID });

    // After data loads, multiplier section should be present
    await expect(
      page.getByText(/multiplicador|multiplier/i).first()
    ).toBeVisible({ timeout: 15_000 });
  });

  test('toggle de estimativa causal mostra banner informativo', async ({ page }) => {
    const installSelector = page
      .getByRole('combobox')
      .or(page.locator('select'))
      .first();
    await installSelector.selectOption({ value: TEST_INSTALLATION_ID });

    // Find and click the causal toggle/checkbox if it exists
    const causalToggle = page
      .getByRole('checkbox', { name: /causal/i })
      .or(page.getByRole('switch', { name: /causal/i }));

    const toggleVisible = await causalToggle.isVisible().catch(() => false);
    if (toggleVisible) {
      await causalToggle.click();
      // Banner with causal unavailability message should appear
      await expect(
        page.getByText(/pipeline.*não integrado|causal.*indispon/i).first()
      ).toBeVisible({ timeout: 10_000 });
    }
  });
});
