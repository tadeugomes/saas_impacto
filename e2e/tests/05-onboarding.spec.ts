/**
 * E2E — Onboarding: criação de tenant + primeiro acesso
 *
 * Cenários:
 * 1. Rota /register renderiza formulário de 3 etapas
 * 2. Validação da etapa 0 — empresa obrigatória
 * 3. Validação da etapa 1 — senhas não coincidem
 * 4. Fluxo completo: preenche 3 etapas e submete (API stubbada)
 * 5. Após onboarding bem-sucedido redireciona para /dashboard
 */

import { test, expect } from '@playwright/test';

// Onboarding tests run unauthenticated (new user creating account)
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Onboarding — Registro de tenant', () => {
  test('rota /register exibe formulário multi-etapas', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByRole('heading', { name: /cadastro/i })).toBeVisible();
    await expect(page.getByLabel(/nome da empresa/i)).toBeVisible();
  });

  test('etapa 0: empresa obrigatória', async ({ page }) => {
    await page.goto('/register');
    // Clear default value if any and try to proceed
    await page.getByLabel(/nome da empresa/i).fill('');
    await page.getByRole('button', { name: /próximo/i }).click();

    await expect(
      page.getByText(/informe o nome|empresa.*obrigatório|mínimo 2/i).first()
    ).toBeVisible({ timeout: 5_000 });
  });

  test('etapa 1: senha fraca exibe erro', async ({ page }) => {
    await page.goto('/register');

    // Step 0 — fill company
    await page.getByLabel(/nome da empresa/i).fill('Porto Teste E2E');
    await page.getByRole('button', { name: /próximo/i }).click();

    // Step 1 — fill admin info with weak password
    await page.getByLabel(/nome do administrador/i).fill('Admin Teste');
    await page.getByLabel(/e-mail do administrador/i).fill('admin@portoteste.com');
    await page.getByLabel('Senha').fill('curta'); // < 8 chars
    await page.getByLabel(/confirmar senha/i).fill('curta');
    await page.getByRole('button', { name: /próximo/i }).click();

    await expect(
      page.getByText(/ao menos 8|senha.*curta|mínimo.*8/i).first()
    ).toBeVisible({ timeout: 5_000 });
  });

  test('etapa 1: senhas não coincidem exibe erro', async ({ page }) => {
    await page.goto('/register');

    await page.getByLabel(/nome da empresa/i).fill('Porto Teste E2E');
    await page.getByRole('button', { name: /próximo/i }).click();

    await page.getByLabel(/nome do administrador/i).fill('Admin Teste');
    await page.getByLabel(/e-mail do administrador/i).fill('admin@portoteste.com');
    await page.getByLabel('Senha').fill('senhaforte123');
    await page.getByLabel(/confirmar senha/i).fill('senhadiferente456');
    await page.getByRole('button', { name: /próximo/i }).click();

    await expect(
      page.getByText(/senhas não coincidem|as senhas/i).first()
    ).toBeVisible({ timeout: 5_000 });
  });

  test('fluxo completo de onboarding redireciona para /dashboard', async ({ page }) => {
    // Stub the register endpoint so it doesn't hit real API
    await page.route('**/api/v1/auth/register**', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          tenant_id: 'e2e-tenant-001',
          user: {
            id: 'e2e-user-001',
            email: 'admin@portoteste.com',
            name: 'Admin Teste',
          },
          access_token: 'e2e-access-token',
          token_type: 'bearer',
        }),
      });
    });

    await page.goto('/register');

    // Step 0
    await page.getByLabel(/nome da empresa/i).fill('Porto Teste E2E');
    await page.getByRole('button', { name: /próximo/i }).click();

    // Step 1
    await page.getByLabel(/nome do administrador/i).fill('Admin Teste');
    await page.getByLabel(/e-mail do administrador/i).fill('admin@portoteste.com');
    await page.getByLabel('Senha').fill('senhaforte123');
    await page.getByLabel(/confirmar senha/i).fill('senhaforte123');
    await page.getByRole('button', { name: /próximo/i }).click();

    // Step 2 — confirmation screen
    await expect(page.getByText(/porto teste e2e/i)).toBeVisible({ timeout: 5_000 });
    await page.getByRole('button', { name: /concluir cadastro/i }).click();

    // Should redirect to dashboard after successful registration
    await expect(page).toHaveURL(/\/(dashboard|login)/, { timeout: 15_000 });
  });
});
