# Phase 8: CI & Code Quality - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Get CI pipeline green and establish code quality baseline. Fix all linting errors, resolve all pyright strict type errors in api and domain projects, add code coverage Nx targets, and ensure import-linter passes in CI. This is infrastructure/tooling work -- no new features, no frontend code.

</domain>

<decisions>
## Implementation Decisions

### CI Pipeline Strategy
- Use `nx affected` for CI runs (only test/lint/typecheck changed projects). Requires proper base/head ref setup.
- All checks are strictly blocking -- lint, typecheck, test, import-linter, format must all pass to merge. Zero tolerance.
- Cache both Python (uv) and Node (node_modules) dependencies between CI runs for speed.
- Allow Rust toolchain in CI for typeid-python build from source (crates.io access required).
- Current CI has two jobs (lint+typecheck, test). May restructure as needed but the affected + blocking + caching decisions are locked.

### Type Error Resolution
- Fix ALL pyright strict errors in this phase. Clean slate before frontend work. No baseline-and-suppress approach.
- `# type: ignore` allowed pragmatically with justification comment. Each must explain WHY it's necessary (e.g., SQLAlchemy mapper internals, third-party lib limitations).
- For ORM/SQLAlchemy typing: research options, prioritize type safety in domain layer and service layer. ORM adapter layer can use targeted type: ignore where SQLAlchemy types are genuinely incomplete. The signal value is in domain and service layers.
- Report missing type stubs (`reportMissingTypeStubs` enabled). Add py.typed packages or stub packages where available; explicitly ignore the rest.
- Pin pyright version in pyproject.toml for consistent results across dev and CI.
- Add `py.typed` marker to `libs/domain` so downstream consumers get full type information.
- Per-project pyrightconfig.json (api and domain each get their own). Same strict level for both projects.
- Tests must also pass pyright strict -- no relaxed mode for test files.
- Full type annotations everywhere: all fixtures get return types, dependency injection fully typed, model_validate calls use explicit types.
- Protocols in domain layer remain structural-only (no @runtime_checkable).

### Code Coverage Policy
- Coverage is a tool for Claude to identify gaps and improve both tests and code -- not just a metric for CI.
- Report only -- no enforced minimum threshold. CI reports coverage but does not fail on low numbers.
- Coverage for both api and domain projects.
- Terminal summary output only. No HTML artifacts.
- Separate Nx `coverage` target (not integrated into `test`). `npx nx coverage api` runs tests with coverage; `npx nx test api` runs fast without overhead.

### Claude's Discretion
- Branch coverage vs line-only: Claude picks what gives better signal for improving tests.
- Coverage tool choice (pytest-cov is standard, but Claude can evaluate alternatives).

### Lint & Format Standards
- Comprehensive ruff rule set: E, W, F, I, N, UP, B, SIM, C4, RUF (and similar). Catches common bugs, enforces modern Python, import sorting.
- CI reports lint errors only (no auto-fix). Developers run `ruff --fix` locally.
- Claude's discretion on: docstring rules (D), line length, security rules (S/bandit), pytest style rules (PT), import section ordering, pre-commit hooks.

</decisions>

<specifics>
## Specific Ideas

- Coverage purpose: "for you [Claude] to be able to improve both the test and code" -- coverage exists as an improvement signal, not a gatekeeping metric.
- The user wants maximum type safety signal from domain and service layers. ORM adapter typing is secondary.
- All checks blocking means this phase must deliver a fully green CI before it's complete.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 08-ci-code-quality*
*Context gathered: 2026-02-09*
