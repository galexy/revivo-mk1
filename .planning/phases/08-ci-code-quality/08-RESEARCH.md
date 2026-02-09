# Phase 8: CI & Code Quality - Research

**Researched:** 2026-02-09
**Domain:** CI pipeline, Python type checking, linting, code coverage, Nx monorepo tooling
**Confidence:** HIGH

## Summary

Phase 8 is infrastructure/tooling work to get the CI pipeline green and establish a code quality baseline. The codebase currently has **72 pyright errors in api** (src/ only), **7 errors in domain**, **214 ruff lint errors in api**, **33 in domain**, **26 files needing reformatting**, and **16 additional pyright errors across both test suites**. Import-linter already passes (2/2 contracts kept). Tests already pass (252 api, 192 domain = 444 total).

The work falls into five distinct areas: (1) fixing all pyright strict errors, (2) fixing all ruff lint errors, (3) adding per-project pyrightconfig.json files that include tests, (4) adding code coverage Nx targets, and (5) restructuring CI with `nx affected`, caching, and all checks blocking.

**Primary recommendation:** Fix errors in dependency order -- domain pyright first (7 errors), then domain lint (33), then api pyright (72 + 11 route narrowing), then api lint (214), then add coverage targets, then restructure CI. Reformatting (26 files) should be done early as a separate atomic step since `ruff format --fix` is fully automated.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CI Pipeline Strategy:**
- Use `nx affected` for CI runs (only test/lint/typecheck changed projects). Requires proper base/head ref setup.
- All checks are strictly blocking -- lint, typecheck, test, import-linter, format must all pass to merge. Zero tolerance.
- Cache both Python (uv) and Node (node_modules) dependencies between CI runs for speed.
- Allow Rust toolchain in CI for typeid-python build from source (crates.io access required).
- Current CI has two jobs (lint+typecheck, test). May restructure as needed but the affected + blocking + caching decisions are locked.

**Type Error Resolution:**
- Fix ALL pyright strict errors in this phase. Clean slate before frontend work. No baseline-and-suppress approach.
- `# type: ignore` allowed pragmatically with justification comment. Each must explain WHY it's necessary.
- For ORM/SQLAlchemy typing: research options, prioritize type safety in domain layer and service layer. ORM adapter layer can use targeted type: ignore where SQLAlchemy types are genuinely incomplete.
- Report missing type stubs (`reportMissingTypeStubs` enabled). Add py.typed packages or stub packages where available; explicitly ignore the rest.
- Pin pyright version in pyproject.toml for consistent results across dev and CI.
- Add `py.typed` marker to `libs/domain` so downstream consumers get full type information.
- Per-project pyrightconfig.json (api and domain each get their own). Same strict level for both projects.
- Tests must also pass pyright strict -- no relaxed mode for test files.
- Full type annotations everywhere: all fixtures get return types, dependency injection fully typed, model_validate calls use explicit types.
- Protocols in domain layer remain structural-only (no @runtime_checkable).

**Code Coverage Policy:**
- Coverage is a tool for Claude to identify gaps -- not just a metric for CI.
- Report only -- no enforced minimum threshold.
- Coverage for both api and domain projects.
- Terminal summary output only. No HTML artifacts.
- Separate Nx `coverage` target (not integrated into `test`).

**Lint & Format Standards:**
- Comprehensive ruff rule set: E, W, F, I, N, UP, B, SIM, C4, RUF (and similar).
- CI reports lint errors only (no auto-fix). Developers run `ruff --fix` locally.

### Claude's Discretion

- Branch coverage vs line-only: Claude picks what gives better signal.
- Coverage tool choice (pytest-cov is standard, but Claude can evaluate alternatives).
- Docstring rules (D), line length, security rules (S/bandit), pytest style rules (PT), import section ordering, pre-commit hooks.

### Deferred Ideas (OUT OF SCOPE)

None specified in CONTEXT.md.
</user_constraints>

## Standard Stack

### Core (already installed)

| Tool | Version | Purpose | Status |
|------|---------|---------|--------|
| pyright | 1.1.408 | Static type checker (strict mode) | Installed, 79 errors in src/ + tests |
| ruff | 0.14.14 | Linter + formatter | Installed, 247 lint errors + 26 format violations |
| pytest-cov | >=6.0.0 | Coverage plugin for pytest | Installed (in dev deps) |
| import-linter | >=2.1.0 | Architecture enforcement | Installed, passing (2/2 contracts) |
| pytest | >=8.3.0 | Test framework | Installed, 444 tests passing |

### Supporting (no new installs needed)

| Tool | Purpose | Notes |
|------|---------|-------|
| coverage.py | Backend for pytest-cov | Already configured in `[tool.coverage.run]` with branch=true |
| nrwl/nx-set-shas@v4 | GitHub Action for nx affected base/head SHA resolution | Need to add to CI workflow |
| astral-sh/setup-uv@v4+ | GitHub Action for uv with built-in caching | Already used, need to enable caching |

### Alternatives Considered

| Instead of | Could Use | Why Not |
|------------|-----------|---------|
| pytest-cov | coverage.py directly | pytest-cov integrates seamlessly with pytest; already installed |
| pyright pinned | basedpyright | Unnecessary complexity; pyright 1.1.408 works, just pin it |

**Installation:** No new packages needed. All tools are already in root pyproject.toml dev dependencies.

## Architecture Patterns

### Per-Project Pyright Configuration

Each project gets its own `pyrightconfig.json` at the project root. This is the standard pyright approach for monorepos.

**`apps/api/pyrightconfig.json`:**
```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.12",
  "include": ["src", "tests"],
  "venvPath": "../..",
  "venv": ".venv",
  "reportMissingTypeStubs": true,
  "pythonPlatform": "Linux"
}
```

**`libs/domain/pyrightconfig.json`:**
```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.12",
  "include": ["domain", "tests"],
  "venvPath": "../..",
  "venv": ".venv",
  "reportMissingTypeStubs": true,
  "pythonPlatform": "Linux"
}
```

The pyright version should be pinned in the root `pyproject.toml` to a specific version (e.g., `"pyright==1.1.408"`) so CI and dev machines get identical results.

Source: [pyright configuration docs](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)

### Nx Target Updates for Typecheck and Coverage

The typecheck targets currently only check `src/` (api) or `domain/` (domain). They must be updated to check both source and tests:

```json
{
  "typecheck": {
    "command": "uv run --package personal-finance-api pyright",
    "cwd": "{projectRoot}"
  }
}
```

With a `pyrightconfig.json` in the project root that specifies `include: ["src", "tests"]`, pyright will find and use it automatically when invoked from cwd without explicit path arguments.

New coverage target pattern:
```json
{
  "coverage": {
    "executor": "nx:run-commands",
    "options": {
      "command": "uv run --package personal-finance-api pytest tests/ -v --tb=short --cov=src --cov-config=../../pyproject.toml --cov-report=term-missing --cov-branch",
      "cwd": "{projectRoot}"
    }
  }
}
```

### CI Pipeline Pattern with nx affected

```yaml
- uses: nrwl/nx-set-shas@v4
  with:
    main-branch-name: main

- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Required for nx affected

- uses: astral-sh/setup-uv@v4
  with:
    enable-cache: true
    cache-dependency-glob: |
      **/pyproject.toml
      uv.lock

- uses: actions/setup-node@v4
  with:
    node-version: "20"
    cache: "npm"

- run: npx nx affected -t lint typecheck test --base=$NX_BASE --head=$NX_HEAD
```

Source: [nrwl/nx-set-shas](https://github.com/nrwl/nx-set-shas), [Nx affected docs](https://nx.dev/docs/features/ci-features/affected)

### Anti-Patterns to Avoid

- **Suppressing errors with `# type: ignore` on fixable code:** Only use on genuinely unfixable SQLAlchemy imperative mapping issues. Every suppression needs a comment explaining why.
- **Running `ruff format` in CI as auto-fix:** CI should only CHECK formatting, never auto-fix. Format check is `ruff format --check .`
- **Adding `--no-strict` for test files:** The decision is strict mode everywhere, including tests. Fix the errors, don't relax the checker.

## Current Error Inventory

### Pyright Errors (72 api src/ + 7 domain + 16 tests = 95 total)

**Domain (7 errors in src, 13 in tests = 20 total):**
| Error Type | Count | Files | Root Cause | Fix Strategy |
|-----------|-------|-------|------------|-------------|
| `reportReturnType` (Self vs concrete) | 5 | `money.py` | Methods return `Money(...)` but annotated as `-> Self`. Pyright strict rejects `Money` for `Self` in case of subclassing. | Change `-> Self` to `-> "Money"` since Money is `frozen=True` and won't be subclassed. Or use `type(self)(...)` pattern. |
| `reportReturnType` (Self vs concrete) | 2 | `rewards_balance.py` | Same pattern as Money. | Same fix. |
| `reportInvalidTypeVarUse` | 1 | `ports/repository.py` | TypeVar `ID` in Protocol should be contravariant. | Change to `ID = TypeVar("ID", contravariant=True)` or remove Generic usage since concrete repos don't use it. |
| `reportArgumentType` (str literal != Decimal) | 9 | `test_split_line.py` | Tests pass string literals where `Decimal` expected. | Wrap with `Decimal("...")`. |
| `reportOptionalMemberAccess` | 1 | `test_account.py` | Accessing `.name` on potentially None value. | Add assert or None check. |
| `reportAttributeAccessIssue` (frozen assign) | 2 | `test_entity_id.py` | Tests intentionally assign to frozen dataclass. | Use `object.__setattr__` or restructure test. |

**API src/ (72 errors):**
| Error Type | Count | Files | Root Cause | Fix Strategy |
|-----------|-------|-------|------------|-------------|
| `reportArgumentType` (bool for Column filter) | 34 | All repositories | SQLAlchemy imperative mapping: `DomainClass.attribute == value` returns Python `bool` to pyright, not `ColumnElement[bool]`. | Use table-column references (`accounts.c.user_id == str(user_id)`) or `# type: ignore[reportArgumentType]` with justification. |
| `reportAttributeAccessIssue` (.desc() on Python type) | 10 | transaction.py, payee.py, account.py | Same root cause: `Transaction.effective_date.desc()` -- pyright sees `date` not Column. | Use `transactions.c.effective_date.desc()` or `# type: ignore`. |
| `reportAttributeAccessIssue` (mapper attribute assign) | 18 | `mappers.py` | Value object decomposition assigns attributes SQLAlchemy injected at runtime, not on domain class. | `# type: ignore[reportAttributeAccessIssue]` -- this is genuinely dynamic. Mapper injects these attrs. |
| `reportArgumentType` (Union narrowing) | 11 | `routes/accounts.py` | `_handle_error()` raises but returns `None`, not `NoReturn`. Type not narrowed after isinstance check. | Add `-> NoReturn` return type to `_handle_error()`. |
| `reportAttributeAccessIssue` (.rowcount) | 3 | `refresh_token.py` | `Result[Any]` doesn't expose `.rowcount` in type stubs. | `# type: ignore[reportAttributeAccessIssue]` -- known SQLAlchemy stubs gap for update/delete results. |

**API tests/ (3 errors):**
| Error Type | Count | Files | Root Cause | Fix Strategy |
|-----------|-------|-------|------------|-------------|
| `reportUndefinedVariable` | 3 | `conftest.py` | Forward reference `"Money"` in fixture return types without import. | Import Money at module level (or use `TYPE_CHECKING` import). |

### Ruff Lint Errors (214 api + 33 domain = 247 total)

**API (214 errors):**
| Rule | Count | Description | Fix Strategy |
|------|-------|-------------|-------------|
| DTZ011 | 47 | `datetime.date.today()` used | Replace with `datetime.now(UTC).date()` |
| B008 | 38 | `Depends()` in default args | Add `extend-immutable-calls = ["fastapi.Depends", "fastapi.Query", "fastapi.Header"]` to ruff config |
| ARG002 | 28 | Unused method argument | Add `_` prefix or remove unused args |
| I001 | 24 | Import block unsorted | `ruff --fix` (auto-fixable) |
| ARG001 | 21 | Unused function argument | Add `_` prefix |
| TID252 | 19 | Relative imports (from ..schemas) | Convert to absolute imports or add exception for this pattern |
| SLF001 | 12 | Private member access (`_collected_events`) | Add `_` prefix removal where appropriate, or configure allowed private accesses |
| B904 | 7 | `raise X from Y` missing | Add explicit exception chaining |
| F401 | 6 | Unused import | Remove or move to `TYPE_CHECKING` |
| F821 | 3 | Undefined name | Fix forward references |
| TC002/TC001 | 3 | Move import to TYPE_CHECKING | Move import |
| PT012 | 2 | pytest.raises block too broad | Narrow the raises block |
| SIM105/SIM102 | 2 | Simplify try/except/if | Refactor |
| RUF022 | 1 | `__all__` not sorted | Sort |
| RET505 | 1 | Unnecessary elif after return | Simplify |
| N806 | 1 | Variable in function should be lowercase | Rename |

**Domain (33 errors):**
| Rule | Count | Description | Fix Strategy |
|------|-------|-------------|-------------|
| RUF043 | 9 | pytest.raises match= with unescaped regex metacharacters | Use raw strings `r"..."` |
| PT011 | 7 | pytest.raises too broad | Add `match=` parameter |
| I001 | 6 | Import block unsorted | `ruff --fix` (auto-fixable) |
| PIE790 | 5 | Unnecessary `pass` in class body | Remove pass |
| F401 | 3 | Unused import | Remove |
| SIM300 | 1 | Yoda condition | Flip comparison |
| RUF022 | 1 | `__all__` not sorted | Sort |
| N818 | 1 | Exception class name not ending in Error | Rename or suppress |

### Format Violations (26 files)

All fixable with `ruff format .` -- a single automated command.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CI SHA resolution | Custom git diff logic | `nrwl/nx-set-shas@v4` | Handles merge commits, force pushes, first-run fallback |
| uv caching in CI | `actions/cache` with manual paths | `astral-sh/setup-uv` `enable-cache: true` | Built-in, handles cache key computation from lock files |
| Node caching in CI | Manual cache setup | `actions/setup-node` `cache: "npm"` | Built-in npm cache support |
| Coverage reporting | Custom pytest plugins | `pytest-cov` with `--cov-report=term-missing` | Standard, already configured |
| Type stub generation | Hand-typed stubs for SQLAlchemy | SQLAlchemy's built-in stubs (ships with 2.0+) | SA 2.0 is PEP 561 compliant, includes py.typed |

**Key insight:** SQLAlchemy 2.0+ ships its own type stubs. The pyright errors are NOT from missing stubs -- they're from using imperative mapping where pyright can't see that class attributes become Column descriptors at runtime. This is a known limitation. The fix is targeted `# type: ignore` in the ORM adapter layer, or switching to table-column references (`table.c.column`) for queries.

## Common Pitfalls

### Pitfall 1: SQLAlchemy Imperative Mapping vs Pyright

**What goes wrong:** Pyright sees domain class attributes as their declared Python types (e.g., `str`, `date`, `Money`). After imperative mapping, these become SQLAlchemy `InstrumentedAttribute` objects at runtime. Expressions like `Account.user_id == str(user_id)` return `ColumnElement[bool]` at runtime but pyright thinks they return `bool`.

**Why it happens:** Imperative mapping is a runtime transformation that no type checker can follow. Unlike declarative mapping with `Mapped[str]`, imperative mapping preserves the original class type annotations.

**How to avoid:** Two strategies:
1. **Table-column references in repositories:** Use `accounts.c.user_id == str(user_id)` instead of `Account.user_id == str(user_id)`. The `Table.c` accessor is properly typed. However, this changes the query style.
2. **Targeted type: ignore in ORM adapter layer:** Add `# type: ignore[reportArgumentType]  # SQLAlchemy imperative mapping: Column comparison` to each query line. This is the least disruptive approach.

**Recommendation:** Use approach #2 (targeted type: ignore) for the repository layer. The CONTEXT allows this: "ORM adapter layer can use targeted type: ignore where SQLAlchemy types are genuinely incomplete." Add a comment explaining the pattern at the top of each repository module.

**Warning signs:** Any `reportArgumentType` error in a repository file involving `bool` vs `_ColumnExpressionArgument[bool]`.

### Pitfall 2: Self Return Type in Frozen Dataclasses

**What goes wrong:** Methods like `Money.__add__` return `Money(...)` but are typed as `-> Self`. Pyright strict rejects this because if someone subclassed Money, `Self` would be the subclass type, but the method returns the base `Money`.

**Why it happens:** Using `Self` implies subclass compatibility. Frozen dataclasses with `slots=True` can't be meaningfully subclassed, but pyright doesn't know the design intent.

**How to avoid:** Either:
1. Change return type from `Self` to `"Money"` (concrete type) -- honest about no subclassing
2. Use `type(self)(...)` constructor pattern -- preserves Self contract

**Recommendation:** Change to concrete return types. `Money` is `frozen=True, slots=True` and will never be subclassed. The `Self` annotation was aspirational but incorrect.

### Pitfall 3: NoReturn for Error Handlers

**What goes wrong:** After `if isinstance(result, AccountError): _handle_error(result)`, pyright still thinks `result` could be `AccountError | Account` because `_handle_error` returns `None`, not `NoReturn`.

**Why it happens:** Without `NoReturn` annotation, pyright doesn't know the function always raises.

**How to avoid:** Annotate `_handle_error` with `-> NoReturn` (from `typing`). This tells pyright the function never returns normally, enabling type narrowing in the caller.

**Warning signs:** 11 identical errors in `routes/accounts.py` about union types.

### Pitfall 4: CI Fetch Depth for nx affected

**What goes wrong:** `nx affected` needs git history to compare base and head commits. Default `actions/checkout` does a shallow clone (fetch-depth: 1).

**Why it happens:** GitHub Actions optimizes for speed with shallow clones.

**How to avoid:** Set `fetch-depth: 0` in `actions/checkout@v4` to fetch full history. Use `nrwl/nx-set-shas@v4` AFTER checkout to compute proper base SHA.

### Pitfall 5: B008 False Positives with FastAPI Depends

**What goes wrong:** Ruff B008 flags `Depends(get_service)` as a mutable default argument in function signatures. This is a false positive -- FastAPI's dependency injection system specifically requires this pattern.

**Why it happens:** B008 detects function calls in default arguments, which is normally a bug (shared mutable state). But FastAPI `Depends()`, `Query()`, `Header()` are designed for this.

**How to avoid:** Configure ruff to treat these as immutable:
```toml
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["fastapi.Depends", "fastapi.Query", "fastapi.Header", "fastapi.Body", "fastapi.Path"]
```

Source: [ruff B008 docs](https://docs.astral.sh/ruff/rules/function-call-in-default-argument/), [FastAPI issue #1522](https://github.com/fastapi/fastapi/issues/1522)

### Pitfall 6: Relative Imports (TID252) in API Project

**What goes wrong:** 19 TID252 errors for relative imports like `from ..schemas.account import ...` in route files.

**Why it happens:** The ruff TID252 rule flags relative imports from parent modules. The API project uses relative imports within the adapters layer.

**How to avoid:** Two options:
1. Convert all relative imports to absolute (e.g., `from src.adapters.api.schemas.account import ...`)
2. Disable TID252 rule if relative imports are the project convention

**Recommendation:** Convert to absolute imports. This is consistent with CLAUDE.md import conventions (`from src.adapters.api.app import create_app`) and makes the codebase more navigable.

### Pitfall 7: DTZ011 in Test Code

**What goes wrong:** 47 DTZ011 errors for `datetime.date.today()` -- mostly in test files creating test data.

**Why it happens:** Ruff DTZ (datetimez) rules require timezone-aware datetime operations. `date.today()` is not timezone-aware.

**How to avoid:** Replace with `datetime.now(UTC).date()` which is explicitly timezone-aware. For test data, this is a straightforward mechanical replacement.

## Code Examples

### Fix 1: Money Self -> Concrete Return Type

```python
# Before (7 errors in domain)
def __add__(self, other: Self) -> Self:
    self._check_same_currency(other)
    return Money(self.amount + other.amount, self.currency)

# After
def __add__(self, other: "Money") -> "Money":
    self._check_same_currency(other)
    return Money(self.amount + other.amount, self.currency)
```

Note: `_check_same_currency` parameter type should also change from `Self` to `"Money"`.

### Fix 2: NoReturn for Error Handler

```python
# Before (11 errors in routes/accounts.py)
from typing import NoReturn

def _handle_error(error: AccountError) -> NoReturn:
    """Convert AccountError to HTTPException. Always raises."""
    status_map = { ... }
    raise HTTPException(...)
```

### Fix 3: Repository Type Ignore Pattern

```python
# Before (34 reportArgumentType errors across repositories)
stmt = select(Account).where(Account.user_id == str(user_id))

# After -- with targeted type: ignore
stmt = select(Account).where(
    Account.user_id == str(user_id)  # type: ignore[reportArgumentType]  # SQLAlchemy imperative mapping
)
```

### Fix 4: Mapper Attribute Assignment Type Ignore

```python
# Before (18 errors in mappers.py)
obj.opening_balance_amount = obj.opening_balance.amount

# After
obj.opening_balance_amount = obj.opening_balance.amount  # type: ignore[reportAttributeAccessIssue]  # SQLAlchemy-injected attribute from imperative mapping
```

### Fix 5: pytest-cov Configuration

The `[tool.coverage.run]` config already exists in root `pyproject.toml` with `branch = true`. The Nx coverage target needs to reference it:

```json
{
  "coverage": {
    "executor": "nx:run-commands",
    "options": {
      "command": "uv run --package personal-finance-api pytest tests/ --cov=src --cov-config=../../pyproject.toml --cov-report=term-missing --cov-branch",
      "cwd": "{projectRoot}"
    },
    "inputs": [
      "{projectRoot}/**/*.py",
      "{workspaceRoot}/libs/domain/**/*.py"
    ],
    "outputs": []
  }
}
```

### Fix 6: CI Workflow with nx affected and Caching

```yaml
jobs:
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: nrwl/nx-set-shas@v4
        with:
          main-branch-name: main

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
          cache-dependency-glob: |
            **/pyproject.toml
            uv.lock

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - run: npm ci
      - run: uv sync --all-packages

      - run: npx nx affected -t lint typecheck --base=$NX_BASE --head=$NX_HEAD
      - run: uv run ruff format --check .
      - run: uv run lint-imports

  test:
    name: Test
    runs-on: ubuntu-latest
    services:
      postgres: ...
    steps:
      # Same setup as above
      - run: npx nx affected -t test --base=$NX_BASE --head=$NX_HEAD
```

### Fix 7: B008 Configuration

```toml
# Add to pyproject.toml
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = [
    "fastapi.Depends",
    "fastapi.Query",
    "fastapi.Header",
    "fastapi.Body",
    "fastapi.Path",
    "fastapi.Cookie",
    "fastapi.Form",
]
```

## Discretion Decisions (Claude's Recommendations)

### Branch Coverage: YES (already configured)

**Recommendation:** Keep branch coverage enabled.

The root `pyproject.toml` already has `branch = true` in `[tool.coverage.run]`. Branch coverage reveals untested conditional paths that line coverage misses. For a finance app with complex conditional logic (account types, status transitions, error handling), branch coverage provides significantly better signal for test improvement.

### Coverage Tool: pytest-cov (keep current)

**Recommendation:** Use pytest-cov (already installed, already configured).

pytest-cov is the standard. It wraps coverage.py and integrates with pytest. The alternative (running coverage.py directly) provides no benefit here and would require additional Nx target complexity. The existing `[tool.coverage.run]` and `[tool.coverage.report]` configuration is correct.

### Docstring Rules (D): Skip for now

**Recommendation:** Do NOT enable ruff `D` rules in this phase. The codebase already has docstrings on public APIs (a deliberate choice from earlier phases). Adding `D` rules would create hundreds of new errors for formatting nits (missing period, wrong style) without improving code quality. This can be a follow-up if desired.

### Security Rules (S/bandit): Skip for now

**Recommendation:** Do NOT enable ruff `S` rules in this phase. Security rules would flag test fixtures, development configs, and known-safe patterns. Adding them creates noise. Better to add in a dedicated security review phase.

### Pre-commit Hooks: Skip for now

**Recommendation:** Do NOT set up pre-commit hooks in this phase. The phase scope is CI pipeline and code quality baseline. Pre-commit hooks are a developer experience enhancement that can come later. CI is the authoritative gate.

### Ruff Rule Set: Keep Current (with additions)

**Recommendation:** Keep the current comprehensive rule set. Only add:
1. `"W"` (pycodestyle warnings) to the select list -- currently missing
2. `extend-immutable-calls` for B008 false positives
3. Possibly `SIM` (already present) -- verified it's there

The current set already exceeds the CONTEXT minimum. No rules need removal.

### TID252 (Relative Imports): Convert to Absolute

**Recommendation:** Convert the 19 relative imports to absolute imports. This is consistent with the project's import conventions documented in CLAUDE.md.

### SLF001 (Private Member Access): Per-file Ignore in Tests

**Recommendation:** The 12 SLF001 errors are for accessing `_collected_events` in mappers/repositories -- which is by design (the mapper needs to access domain object internals). Options:
1. Add `per-file-ignores` for specific files: `"src/adapters/persistence/**" = ["SLF001"]`
2. Rename `_collected_events` to `collected_events` (but this changes the domain model interface)

Use option 1 -- the persistence adapter layer legitimately accesses domain internals as part of the Data Mapper pattern.

### DTZ011: Add Ignore for Test Code

**Recommendation:** The 47 DTZ011 errors are mostly in test code. While they should be fixed for consistency, consider `per-file-ignores` for test files if the fix volume is too high: `"tests/**" = ["DTZ011"]`. However, since the fix is mechanical (`date.today()` -> `datetime.now(UTC).date()`), fixing is preferred over suppressing.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `mypy` for type checking | `pyright` in strict mode | SQLAlchemy 2.0+ (2023) | Pyright has better incremental performance and stricter checks |
| `types-SQLAlchemy` stubs | SQLAlchemy ships own stubs (PEP 561) | SQLAlchemy 2.0 (2023) | No external stub package needed |
| `flake8` + plugins | `ruff` (all-in-one) | 2023-2024 | Single tool, 10-100x faster |
| Manual CI caching | `setup-uv` built-in cache | 2024+ | Automatic cache key computation |
| `nx run-many` in CI | `nx affected` in CI | Always available | Only runs tasks for changed projects |

**Deprecated/outdated:**
- `mypy` SQLAlchemy plugin: Deprecated in SA 2.0, will be removed in SA 2.1
- `types-SQLAlchemy` package: Unnecessary with SA 2.0+ which ships its own stubs
- `nrwl/nx-set-shas@v3`: Use @v4 which supports Node 20

## Open Questions

1. **Should `npm install` become `npm ci` in CI?**
   - What we know: `npm ci` is faster and deterministic (uses package-lock.json exactly). `npm install` may update lock file.
   - What's unclear: Whether the current `package-lock.json` is in sync.
   - Recommendation: Switch to `npm ci` for CI. It's the standard CI practice.

2. **Should typecheck target use pyrightconfig.json or explicit args?**
   - What we know: If pyrightconfig.json exists in cwd, pyright uses it automatically. No need to pass `src/` as argument.
   - What's unclear: Whether removing the explicit path argument breaks anything.
   - Recommendation: Use pyrightconfig.json (per CONTEXT decision). Update Nx target to just run `pyright` without path arguments. The config file controls includes.

3. **Repository query refactoring vs type: ignore**
   - What we know: 34 errors in repositories could be fixed by using `table.c.column` instead of `DomainClass.column`. But this changes the query pattern used throughout the project.
   - What's unclear: Whether `table.c.column` works with `select(DomainClass)` style queries.
   - Recommendation: Start with `# type: ignore` for this phase. Refactoring queries is a larger change that could break things. The CONTEXT explicitly allows type: ignore in the ORM layer.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: Current error counts from `npx nx lint/typecheck api/domain` (verified 2026-02-09)
- [pyright configuration docs](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)
- [ruff settings](https://docs.astral.sh/ruff/settings/)
- [nrwl/nx-set-shas](https://github.com/nrwl/nx-set-shas) GitHub Action docs
- [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv) GitHub Action docs

### Secondary (MEDIUM confidence)
- [SQLAlchemy imperative mapping typing issues](https://github.com/sqlalchemy/sqlalchemy/issues/10531) - confirmed by codebase inspection
- [FastAPI B008 workaround](https://github.com/fastapi/fastapi/issues/1522) - confirmed with ruff docs
- [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/latest/config.html) - standard docs

### Tertiary (LOW confidence)
- None. All findings verified against codebase or official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools already installed and configured, just need fixing/tuning
- Architecture: HIGH - per-project pyrightconfig.json is standard pyright pattern, verified
- Pitfalls: HIGH - all pitfalls identified from actual errors in the codebase
- Error inventory: HIGH - exact counts from running the tools just now

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (stable tooling, no version changes expected)
