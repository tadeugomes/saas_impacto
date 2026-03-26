import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration — SaaS Impacto Portuário.
 *
 * Staging URL is injected via E2E_BASE_URL (CI) or falls back to local dev server.
 * Authentication state is persisted in e2e/.auth/ to avoid login on every test.
 */

const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:5173';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false, // sequential — avoids shared state conflicts on staging
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ...(process.env.CI ? [['github'] as ['github']] : []),
  ],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Give the app time to render charts and async data
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    // Setup project: authenticate once and save storage state
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },

    // Main E2E suite — uses authenticated session
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  // Start local dev server when not running against staging
  ...(process.env.E2E_BASE_URL
    ? {}
    : {
        webServer: {
          command: 'npm run dev',
          cwd: '../frontend',
          url: BASE_URL,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
      }),
});
