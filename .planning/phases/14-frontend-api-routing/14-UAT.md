---
status: complete
phase: 14-frontend-api-routing
source: 14-01-SUMMARY.md, 14-02-SUMMARY.md, 14-03-SUMMARY.md, 14-04-SUMMARY.md
started: 2026-02-11T06:00:00Z
updated: 2026-02-11T06:42:00Z
---

## Current Test

[testing complete]

## Tests

### 1. OpenAPI Type Generation
expected: Running `npx nx generate-api-types web` produces TypeScript types at `apps/web/src/lib/api-types.generated.ts` with schemas for accounts, transactions, and categories.
result: pass

### 2. Unit Tests Pass
expected: Running `npx nx test web` passes all 38 tests (17 existing auth/app + 21 new API client/error parsing).
result: pass

### 3. TanStack Query Wired Into App
expected: Opening the app in browser shows React Query DevTools floating button in bottom-right corner (dev mode). QueryClientProvider wraps the app.
result: pass

### 4. E2E Smoke Tests Pass
expected: Running Playwright e2e tests (`npx nx e2e web`) with both API and web servers running passes smoke tests including auth fixture (register, verify via Mailpit, login, dashboard access).
result: issue
reported: "setup project doesn't use system chromium, that's a bug"
severity: major
resolution: |
  Fixed 5 bugs during UAT:
  1. Playwright setup project missing launchOptions with system Chromium
  2. getByLabel('Password') strict mode violation (2 elements) - use exact: true
  3. Promise.race with waitForURL throws instead of resolving - use .catch()
  4. Email subject filter 'erif' doesn't match 'Confirm' - added 'onfirm' match
  5. storageState path mismatch (apps/web/ prefix from workspace root vs project root)
  6. Smoke test assertions outdated (heading text, strict selectors, placeholder content)
  7. Token rotation invalidates storageState across parallel tests - combined into single test
  After fixes: 4/4 e2e tests pass (setup + 2 unauthenticated + 1 authenticated)

### 5. API Error Handling
expected: The API error parsing handles both FastAPI error formats.
result: skipped
reason: Already covered by Test 2 (unit tests all pass)

## Summary

total: 5
passed: 3
issues: 1
pending: 0
skipped: 1

## Gaps

- truth: "Playwright e2e tests pass with auth fixture using system Chromium"
  status: fixed
  reason: "User reported: setup project doesn't use system chromium, that's a bug"
  severity: major
  test: 4
  root_cause: "Multiple bugs in e2e infrastructure: missing launchOptions, incorrect selectors, path mismatches, outdated assertions"
  artifacts:
    - path: "apps/web/playwright.config.ts"
      issue: "setup project missing launchOptions with executablePath"
    - path: "apps/web/e2e/auth.setup.ts"
      issue: "Multiple: selector strict mode, Promise.race error handling, subject filter, storageState path"
    - path: "apps/web/e2e/smoke.spec.ts"
      issue: "Outdated assertions, strict mode violations, token rotation across tests"
  missing: []
  debug_session: ""
