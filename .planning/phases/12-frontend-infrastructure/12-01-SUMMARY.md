---
phase: 12-frontend-infrastructure
plan: 01
subsystem: tooling
tags: [pnpm, monorepo, ci, migration]
requires: []
provides:
  - pnpm package manager
  - pnpm workspace configuration
  - CI updated for pnpm
affects:
  - 12-02-react-vite-tailwind-setup
  - 12-03-web-app-scaffold
  - 12-04-theme-foundation
  - 12-05-nx-web-targets
tech-stack:
  added:
    - pnpm: "10.29.2"
  patterns: []
key-files:
  created:
    - pnpm-workspace.yaml
    - .npmrc
    - pnpm-lock.yaml
  modified:
    - package.json
    - .github/workflows/ci.yml
    - .gitignore
  deleted:
    - package-lock.json
decisions: []
metrics:
  duration: 2
  completed: 2026-02-10
---

# Phase 12 Plan 01: pnpm Migration Summary

**One-liner:** Migrated from npm to pnpm with workspace config, lock file conversion, and CI workflow updated.

## What Was Built

Replaced npm with pnpm as the package manager for better monorepo support and stricter dependency resolution before adding frontend dependencies.

**Key artifacts:**

1. **pnpm workspace configuration** (`pnpm-workspace.yaml`)
   - Defines workspace structure: `apps/*`, `libs/*`
   - Enables pnpm workspace features for monorepo

2. **pnpm configuration** (`.npmrc`)
   - `shamefully-hoist=true` for packages that assume hoisting behavior
   - Ensures compatibility with packages expecting flat node_modules

3. **Lock file conversion** (`pnpm-lock.yaml`)
   - Converted from `package-lock.json` using `pnpm import`
   - Deleted old `package-lock.json`
   - All dependencies preserved (mjml, nx)

4. **CI workflow updates** (`.github/workflows/ci.yml`)
   - Added `pnpm/action-setup@v4` step before Node.js setup in both jobs
   - Changed cache from `npm` to `pnpm` in `actions/setup-node`
   - Replaced `npm ci` with `pnpm install --frozen-lockfile`
   - Both quality and test jobs updated

5. **Gitignore updates** (`.gitignore`)
   - Added `.pnpm-store/` to ignore pnpm cache directory

## Technical Implementation

### Migration Process

1. Installed pnpm as dev dependency (global install failed due to permissions)
2. Created `pnpm-workspace.yaml` with workspace structure
3. Created `.npmrc` with `shamefully-hoist=true`
4. Ran `pnpm import` to convert lock file
5. Deleted `package-lock.json`
6. Ran `pnpm install` to verify setup
7. Updated CI workflow for both jobs (quality + test)
8. Added `.pnpm-store/` to `.gitignore`

### Verification

All existing functionality verified after migration:

- `npx nx show projects`: Lists all 4 projects (api, domain, web, ui)
- `npx nx test domain`: 274 tests passed
- `npx nx test api`: 252 tests passed
- `npx nx run-many -t lint typecheck`: 0 errors, 0 warnings

**Python targets unaffected:** Nx targets use `uv run --package` for Python execution. Package manager change only affects Node.js/frontend tooling.

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

**1. Used `pnpm/action-setup@v4` in CI**

- Decision: Use pnpm's official GitHub Action for setup
- Rationale: Recommended approach from pnpm documentation, handles version pinning automatically
- Impact: CI workflow more maintainable, pnpm version managed by action

**2. Added `shamefully-hoist=true` to .npmrc**

- Decision: Enable hoisting in pnpm workspace
- Rationale: Some packages expect flat node_modules structure. Prevents compatibility issues.
- Impact: More npm-like behavior, reduces potential issues with legacy packages

**3. Installed pnpm as dev dependency**

- Decision: Added pnpm to devDependencies instead of global install
- Rationale: Global install failed due to permissions; local install works and is version-controlled
- Impact: pnpm version explicit in package.json, reproducible across environments

## Test Coverage

No new tests required - migration is a tooling change. Verified all existing tests still pass:

- Domain: 274 tests (100% pass rate)
- API: 252 tests (100% pass rate)
- Lint: 0 errors across all projects
- Typecheck: 0 errors, 0 warnings across all projects

## Next Phase Readiness

**Blockers:** None

**Concerns:**

1. **CI verification needed:** GitHub Actions CI must be verified via PR before proceeding. This is the checkpoint - user will create PR to ensure CI passes with pnpm.

2. **pnpm version in CI:** The `pnpm/action-setup@v4` action will use the version from package.json's `packageManager` field if present, or the latest stable version. Consider pinning if version consistency is critical.

**Readiness for 12-02 (React + Vite + Tailwind):** READY after CI verification. pnpm workspace is configured, all quality gates pass, and the structure supports adding frontend packages to `apps/web`.

## Files Changed

**Created:**
- `pnpm-workspace.yaml` (workspace configuration)
- `.npmrc` (pnpm config with shamefully-hoist)
- `pnpm-lock.yaml` (converted lock file)

**Modified:**
- `package.json` (added pnpm dev dependency)
- `.github/workflows/ci.yml` (pnpm setup + install in both jobs)
- `.gitignore` (added .pnpm-store/)

**Deleted:**
- `package-lock.json` (replaced by pnpm-lock.yaml)

## Commit

- `d67be75`: chore(12-01): migrate from npm to pnpm
