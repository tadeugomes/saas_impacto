/**
 * Environment helpers for E2E tests.
 * Credentials come from environment variables so that CI secrets are not hardcoded.
 * Fall back to the seeded staging user for local runs.
 */

export const TEST_USER = {
  email: process.env.E2E_USER_EMAIL ?? 'admin@example.com',
  password: process.env.E2E_USER_PASSWORD ?? 'admin123',
};

/** Municipality ID used for employment multiplier tests (Paranaguá) */
export const TEST_MUNICIPALITY_ID = '4118204';

/** Installation ID used across module tests */
export const TEST_INSTALLATION_ID =
  process.env.E2E_INSTALLATION_ID ?? 'PRNPGA';

/** Base year used for indicator queries */
export const TEST_YEAR = '2023';
