# E2E Tests — SaaS Impacto Portuário

Playwright test suite. Tests run against a live frontend (local dev server or staging).

## Setup

```bash
cd e2e
npm install
npx playwright install chromium
```

## Run locally (against dev server)

```bash
# Terminal 1 — start frontend
cd ../frontend && npm run dev

# Terminal 2 — run tests
cd ../e2e && npm test
```

## Run against staging

```bash
E2E_BASE_URL=https://staging.impacto.example.com \
E2E_API_URL=https://api-staging.impacto.example.com \
E2E_USER_EMAIL=e2e@test.com \
E2E_USER_PASSWORD=senhateste \
npm test
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_BASE_URL` | `http://localhost:5173` | Frontend URL |
| `E2E_API_URL` | derived from base URL on port 8000 | Backend API URL |
| `E2E_USER_EMAIL` | `admin@example.com` | Test user email |
| `E2E_USER_PASSWORD` | `admin123` | Test user password |
| `E2E_INSTALLATION_ID` | `PRNPGA` | Default installation for filter tests |

## Test files

| File | Scenarios |
|------|-----------|
| `tests/auth.setup.ts` | Authenticate once, save session |
| `tests/01-login.spec.ts` | Login redirect, invalid credentials, valid login |
| `tests/02-module1-indicators.spec.ts` | M1 indicator cards, year filter, export button |
| `tests/03-module3-employment.spec.ts` | Employment indicators, multiplier panel, causal toggle banner |
| `tests/04-module5-causal-analysis.spec.ts` | Analysis form, method selector, status polling, DOCX download |
| `tests/05-onboarding.spec.ts` | Register form, validation, full 3-step flow |
| `tests/06-module2-warnings.spec.ts` | Unavailable indicators show warning, not zero |
| `tests/07-navigation.spec.ts` | All 7 modules navigate without fatal error |
| `tests/08-health.spec.ts` | Backend health endpoint, non-empty dashboard |

## CI

The `e2e` job in `.github/workflows/ci.yml` runs on every PR against `main`.
It requires `E2E_BASE_URL` secret pointing to a stable staging environment.
