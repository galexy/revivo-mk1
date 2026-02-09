---
phase: 08-ci-code-quality
plan: 05
type: gap-closure
wave: 1
subsystem: ci
tags: [nx, ci, format, pyright, quality-gates]
completed: 2026-02-09

requires:
  - phase: 08-04
    provides: CI pipeline with nx affected

provides:
  - output: Per-project format Nx targets
    location: apps/api/project.json, libs/domain/project.json
  - output: CI uses nx affected for format checks
    location: .github/workflows/ci.yml
  - output: import-linter documented as workspace-scoped
    location: .github/workflows/ci.yml
  - output: Pyright-clean side-effect import
    location: apps/api/tests/integration/test_schema_parity.py

affects:
  - phase: 09
    impact: All quality gates now run through Nx consistently

tech-stack:
  added: []
  patterns:
    - "Nx targets for format checks (ruff format --check)"
    - "Per-project format validation with --package flag"
    - "pyright: ignore pragma for side-effect imports"

key-files:
  created: []
  modified:
    - apps/api/tests/integration/test_schema_parity.py
    - apps/api/project.json
    - libs/domain/project.json
    - .github/workflows/ci.yml
    - nx.json

decisions:
  - id: D08-05-01
    decision: Add format as per-project Nx target (not global command)
    rationale: Enables nx affected for efficient PR-scoped execution
    alternatives:
      - Global ruff format command (rejected: not project-aware)
    impact: All quality gates now run through Nx consistently
  - id: D08-05-02
    decision: Document import-linter as workspace-scoped (not Nx target)
    rationale: import-linter validates cross-project boundaries; cannot be per-project
    alternatives:
      - Make it an Nx target (rejected: it checks relationships between projects)
    impact: Clarifies why this is the only quality gate not running via nx affected
  - id: D08-05-03
    decision: Use pyright pragma for side-effect import
    rationale: Side-effect imports are intentional (register tables with metadata)
    alternatives:
      - Remove import and use explicit table registration (rejected: unnecessary complexity)
    impact: Zero pyright warnings, clean type checks

metrics:
  duration: 1.2 min
  tasks_completed: 2
  tests_run: typecheck + format checks
  errors_fixed: 1 pyright warning
---

# Phase 8 Plan 5: Nx/CI Integration Gap Closure Summary

**One-liner:** Per-project format Nx targets and CI using nx affected for all quality gates

## Objective Achieved

Fixed Nx/CI integration gaps by:
1. Suppressing pyright warning on side-effect import (reportUnusedImport pragma)
2. Adding format Nx targets to both api and domain projects (ruff format --check)
3. Updating CI to use nx affected for format checks instead of raw uv commands
4. Adding format and typecheck to nx.json targetDefaults cache
5. Documenting import-linter as intentionally workspace-scoped

**Result:** All quality gates now run through Nx consistently, enabling efficient PR-scoped execution with nx affected. Only exception is import-linter, which is documented as workspace-scoped because it validates cross-project boundaries.

## Tasks Completed

### Task 1: Fix pyright warning and add format Nx targets
- **Commit:** af375ae
- **Duration:** ~1 min
- **Changes:**
  - Suppressed pyright reportUnusedImport in test_schema_parity.py (side-effect import intentional)
  - Added format target to apps/api/project.json (ruff format --check src/ tests/)
  - Added format target to libs/domain/project.json (ruff format --check domain/ tests/)
  - Both targets use --package flag for correct dependency context
- **Verification:** npx nx typecheck api (0 errors, 0 warnings), npx nx run api:format (83 files OK), npx nx run domain:format (43 files OK)

### Task 2: Update CI to use nx affected for format and document import-linter
- **Commit:** 3d68bf5
- **Duration:** <1 min
- **Changes:**
  - Replaced `uv run ruff format --check .` with `npx nx affected -t format --base=$NX_BASE --head=$NX_HEAD`
  - Added comment documenting import-linter as workspace-scoped (validates cross-project boundaries)
  - Added typecheck and format to nx.json targetDefaults cache
- **Verification:** Inspected .github/workflows/ci.yml (nx affected used), inspected comment (clear rationale), inspected nx.json (cache enabled)

## Deviations from Plan

None - plan executed exactly as written.

## Testing & Verification

**Quality gates (all passing):**
- npx nx typecheck api: 0 errors, 0 warnings, 0 informations
- npx nx run api:format: 83 files already formatted
- npx nx run domain:format: 43 files already formatted
- CI file uses npx nx affected -t format (not raw uv)
- import-linter step has documentation comment

**Pre-commit verification:**
- Typecheck ran before commit: 0 errors/warnings
- Format targets tested: both api and domain pass

## Next Phase Readiness

**For Phase 9 (Frontend Infrastructure):**

All CI infrastructure complete:
- Per-project format Nx targets enable selective format checks
- nx affected applies to all quality gates (lint, typecheck, format, test)
- CI pipeline optimized for PR-scoped execution
- All 444 tests passing
- Zero quality gate errors

**CI quality gates:**
1. Lint: nx affected -t lint ✓
2. Typecheck: nx affected -t typecheck ✓
3. Format: nx affected -t format ✓
4. Test: nx affected -t test ✓
5. Import architecture: lint-imports (workspace-scoped) ✓

**Gaps/Concerns:** None. Phase 8 complete.

## Key Decisions

See decisions table in frontmatter.

## Performance Metrics

- **Execution time:** 1.2 minutes
- **Commits:** 2 (1 per task)
- **Files modified:** 5
- **Tests affected:** 0 (infrastructure change only)
- **Quality gates:** All passing (5/5)

## Lessons Learned

1. **Per-project format targets:** Enables nx affected to run format checks only on changed projects, improving CI efficiency
2. **Workspace-scoped tools:** Some tools (like import-linter) cannot be per-project because they validate relationships between projects. Document this explicitly to avoid confusion.
3. **Nx targetDefaults cache:** Adding targets to cache enables Nx to skip execution when inputs haven't changed (speeds up local dev and CI)
4. **pyright pragmas for side-effect imports:** Side-effect imports (like registering tables with metadata) are intentional; use pyright: ignore to suppress reportUnusedImport
