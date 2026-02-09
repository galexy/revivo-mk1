---
status: diagnosed
phase: 08-ci-code-quality
source: 08-01-SUMMARY.md, 08-02-SUMMARY.md, 08-03-SUMMARY.md, 08-04-SUMMARY.md
started: 2026-02-09T08:00:00Z
updated: 2026-02-09T08:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Pyright strict passes with zero errors (domain)
expected: Running `npx nx typecheck domain` completes with zero errors.
result: pass

### 2. Pyright strict passes with zero errors (api)
expected: Running `npx nx typecheck api` completes with zero errors.
result: issue
reported: "i see one warning"
severity: minor

### 3. Ruff lint passes with zero errors (domain)
expected: Running `npx nx lint domain` completes with zero errors.
result: pass

### 4. Ruff lint passes with zero errors (api)
expected: Running `npx nx lint api` completes with zero errors.
result: pass

### 5. Ruff format check passes
expected: Running `uv run ruff format --check .` shows all files already formatted (no changes needed).
result: issue
reported: "shouldn't that be an nx command?"
severity: minor

### 6. import-linter passes
expected: Running `uv run lint-imports` passes all architecture contracts (2/2 contracts OK).
result: issue
reported: "same thing, shouldn't that be an nx command too?"
severity: minor

### 7. All tests pass (domain)
expected: Running `npx nx test domain` passes all 192 domain tests.
result: pass

### 8. All tests pass (api)
expected: Running `npx nx test api` passes all 252 API tests.
result: pass

### 9. Coverage targets work
expected: Running `npx nx coverage api` and `npx nx coverage domain` produce coverage reports with branch coverage. API should show ~81%, domain ~48%.
result: issue
reported: "pass, but 48% for domain is very low"
severity: minor

### 10. CI workflow file exists and is valid
expected: `.github/workflows/ci.yml` exists with two jobs (quality and test), uses nx affected, has uv+npm caching, and all quality gates are blocking.
result: pass

## Summary

total: 10
passed: 6
issues: 5
pending: 0
skipped: 0
skipped: 0

## Gaps

- truth: "npx nx typecheck api completes with zero errors and zero warnings"
  status: failed
  reason: "User reported: i see one warning"
  severity: minor
  test: 2
  root_cause: "test_schema_parity.py line 29 has side-effect import of tables module suppressed with noqa: F401 but pyright uses separate reportUnusedImport diagnostic. executionEnvironments sets it to warning (not false) for tests/"
  artifacts:
    - path: "apps/api/tests/integration/test_schema_parity.py"
      issue: "Side-effect import needs pyright: ignore[reportUnusedImport] alongside noqa: F401"
  missing:
    - "Add # pyright: ignore[reportUnusedImport] to line 29"
  debug_session: ""
- truth: "Ruff format check should be an Nx target, not a bare uv command"
  status: failed
  reason: "User reported: shouldn't that be an nx command?"
  severity: minor
  test: 5
  root_cause: "Phase 8 added format checking to CI via raw 'uv run ruff format --check .' but never created per-project Nx format targets in project.json"
  artifacts:
    - path: "apps/api/project.json"
      issue: "Missing format target"
    - path: "libs/domain/project.json"
      issue: "Missing format target"
    - path: ".github/workflows/ci.yml"
      issue: "Line 61 uses raw uv command instead of nx affected -t format"
  missing:
    - "Add format target to apps/api/project.json and libs/domain/project.json"
    - "Update CI to use npx nx affected -t format"
  debug_session: ""
- truth: "import-linter should be an Nx target, not a bare uv command"
  status: failed
  reason: "User reported: same thing, shouldn't that be an nx command too?"
  severity: minor
  test: 6
  root_cause: "import-linter checks workspace-wide architecture boundaries (cross-project), so it doesn't naturally map to a single Nx project. However, it could be a workspace-level target or at minimum documented as intentionally workspace-scoped."
  artifacts:
    - path: ".github/workflows/ci.yml"
      issue: "Line 64 uses raw uv command for lint-imports"
  missing:
    - "Either add lint-imports as workspace-level Nx target or document why it stays as raw command"
  debug_session: ""
- truth: "type: ignore comments should not paper over fixable type issues"
  status: failed
  reason: "User reported: categories.py lines 119-120 have type: ignore because get_category_tree returns loosely typed dict instead of TypedDict"
  severity: minor
  test: 2
  root_cause: "get_category_tree returns dict[str, list[Category] | dict[str, list[Category]]] — a union-valued dict where every key has the same union type. Accessing tree['root'] and tree['children'] requires type: ignore[assignment] to narrow. The proper fix is a CategoryTree TypedDict with distinct types per key."
  artifacts:
    - path: "apps/api/src/application/services/category_service.py"
      issue: "Return type should be CategoryTree TypedDict, not dict[str, union]"
    - path: "apps/api/src/adapters/api/routes/categories.py"
      issue: "Lines 119-120 have unnecessary type: ignore[assignment] due to weak return type"
  missing:
    - "Create CategoryTree TypedDict with root: list[Category] and children: dict[str, list[Category]]"
    - "Update get_category_tree return type to CategoryTree"
    - "Remove type: ignore[assignment] from categories.py lines 119-120"
  debug_session: ""
- truth: "Domain coverage should be higher than 48%"
  status: failed
  reason: "User reported: pass, but 48% for domain is very low"
  severity: minor
  test: 9
  root_cause: "542 of 1059 statements missed. 95% of misses come from 16 files at 0% coverage: (1) Transaction/Category/Payee models have no domain-level unit tests (268 stmts) -- they rely on API integration tests only; (2) All port Protocol interfaces are 0% (166 stmts) -- pure interfaces with no logic; (3) Transaction events untested (55 stmts). If ports excluded and model tests added, coverage would reach ~85-90%."
  artifacts:
    - path: "libs/domain/domain/model/transaction.py"
      issue: "144 statements, 0% coverage, no domain unit tests"
    - path: "libs/domain/domain/model/category.py"
      issue: "88 statements, 0% coverage, no domain unit tests"
    - path: "libs/domain/domain/model/payee.py"
      issue: "36 statements, 0% coverage, no domain unit tests"
  missing:
    - "Add test_transaction.py, test_category.py, test_payee.py to domain unit tests"
    - "Consider excluding domain/ports/ from coverage measurement (Protocol interfaces)"
  debug_session: ""
