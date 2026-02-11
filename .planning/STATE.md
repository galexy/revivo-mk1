# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-29)

**Core value:** Own your financial data and access it anywhere through any interface - web, API, CLI, or AI. Your data, your tools, no vendor lock-in.
**Current focus:** Phase 15 (API Integration Validation) - Complete

## Current Position

Phase: 15 of 32 (API Integration Validation)
Plan: 8 of 8
Status: Complete
Last activity: 2026-02-11 - Completed 15-08-PLAN.md (UAT via Chrome DevTools MCP)

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 79
- Average duration: 4.4 min
- Total execution time: 7.85 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 6 | 32 min | 5.3 min |
| 02-account-domain | 6 | 62 min | 10.3 min |
| 03-transaction-domain | 7 | 35 min | 5.0 min |
| 03.1-split-identity-validation-fixes | 4 | 21 min | 5.3 min |
| 03.2-add-missing-patch-test-cases | 3 | 7 min | 2.3 min |
| 04-authentication-infrastructure | 8 | 46 min | 5.8 min |
| 04.1-test-schema-parity | 2 | 8 min | 4.0 min |
| 04.2-current-user-metadata-endpoint | 1 | 7 min | 7.0 min |
| 05-domain-event-publishing | 3 | 14 min | 4.7 min |
| 06-transactional-email-infrastructure | 5 | 22 min | 4.4 min |
| 07-nx-monorepo-restructure | 4 | 50 min | 12.5 min |
| 08-ci-code-quality | 5 | 56 min | 11.2 min |
| 09-type-safety-test-cleanup | 1 | 3 min | 3.0 min |
| 10-value-object-orm-mapping | 1 | 6 min | 6.0 min |
| 11-domain-test-coverage | 1 | 5 min | 5.0 min |
| 12-frontend-infrastructure | 6 | 24 min | 4.0 min |
| 13-login-ui | 6 | 49 min | 8.2 min |
| 14-frontend-api-routing | 4 | 13 min | 3.3 min |
| 15-api-integration-validation | 8 | 50 min | 6.3 min |

**Recent Trend:**
- Last 5 plans: 15-04 (6 min), 15-05 (1 min), 15-06 (7 min), 15-07 (13 min), 15-08 (11 min)
- Trend: Phase 15 complete. All 8 plans executed, UAT passed 6/6 flows.

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Tailwind v4 CSS-first @theme syntax (not tailwind.config.js)
- shadcn/ui CSS variable naming: HSL values without hsl() wrapper
- Self-hosted fonts via Fontsource (no external CDN dependencies)
- ESLint 9 flat config excludes Python projects (apps/api, libs/domain)
- Dark mode via .dark class on documentElement with localStorage persistence
- Lazy state initializer for localStorage reads (not useEffect setState)
- Internal package pattern for libs/ui (no build step, direct TS imports via tsconfig paths)
- Refresh cookie samesite=lax (not strict) for cross-origin CORS compatibility
- Cookie path /auth (not /auth/refresh) so both refresh and logout endpoints receive cookie
- remember_me parameter controls session cookie vs 30-day persistent cookie
- failedQueue pattern for concurrent 401s (first refreshes, others wait and retry)
- Module-level accessToken storage with getAccessToken/setAccessToken for AuthContext
- window.location.href for logout redirect (full state reset vs router.navigate)
- Auth guard logic in route beforeLoad (not component useEffect) for type-safe redirects
- AbortController cleanup in refresh useEffect prevents StrictMode double-mount race
- Form-encoded URLSearchParams body for /auth/token (OAuth2PasswordRequestForm compatibility)
- isLoading state starts true, prevents flash of login page during auth check
- PasswordInput uses forwardRef for react-hook-form compatibility, tabIndex=-1 on toggle button
- TanStack Router validateSearch requires explicit return type for optional params
- Registration success shows verification notice, does NOT auto-login per user decision
- Server errors displayed as destructive banner above submit button (not toast)
- validateSearch with optional types ({ expired?: boolean }) makes search params optional for type-safe navigation
- Email resend on expired token uses POST /auth/register (enumeration protection via always-202)
- UserMenu generates initials from first + last word of display_name (max 2 chars)
- Logout is immediate (no confirmation dialog) per UX specification
- Session expired message shown via /login?expired=true from api.ts interceptor
- DashboardPage owns sidebar + header layout (dark mode state managed there)
- shadcn/ui new-york style for component aesthetics
- .gitignore allows libs/ui/src/lib/ (shadcn convention) while blocking Python lib/
- Vitest (not Jest) for component testing - native Vite integration
- window.matchMedia mock in test-setup.ts for theme detection in JSDOM
- Playwright chromium-only configuration for e2e smoke tests
- Explicit Nx targets (lint, format, e2e) complement @nx/vite inferred targets
- Testing Library queries: use getAllByText for duplicate elements (DialogTitle + content)
- Wizard step tests query unique form elements (labelText) not generic headings
- waitFor uses queryByX (returns null) not getByX (throws) for async element appearance
- Playwright auth setup uses Mailpit REST API to extract verification token from email
- Setup project as dependency pattern (runs once, saves storageState for all tests)
- E2E account tests use wizard UI (not API) for test data setup (page.request doesn't inherit storageState cookies)
- Account wizard radio buttons need getByLabel().click({ force: true }) (labels intercept pointer events)
- Unique account names with Date.now() timestamps prevent test data collisions
- Unauthenticated tests override storageState with empty cookies/origins
- QueryClient stale times per entity: 30s default, 60s accounts, 15s transactions, 5min categories
- QueryClientProvider wraps AuthProvider (auth context can use queries if needed)
- API accepts amount as number | string (MoneySchema-Input), pass form string values directly
- Rewards accounts use rewards_balance with value/unit, not opening_balance with amount/currency
- Mutation hooks invalidate queryKeys.accounts.lists() in onSettled for cache refresh
- useDeleteAccount also removeQueries for specific account detail query
- Account detail route nested under dashboard (/dashboard/accounts/$accountId) for layout inheritance
- AccountSidebar uses useParams to detect active account from route params for highlighting
- Edit mode skips step 0 in multi-step wizards (immutable field like account type)
- Form data accumulation pattern: merge current + accumulated on navigation for persistence
- Auth context stays React Context (TanStack Query for server state only)
- MSW for API mocking (intercepts at network boundary, tests full axios chain)
- Test fixtures use generated OpenAPI types for type safety
- MSW handlers use full URL (baseURL in axios instance)
- API client unwraps AxiosResponse.data for cleaner function signatures
- Route loader pattern: ensureQueryData (not prefetchQuery) for instant navigation
- Query keys follow TkDodo v5 hierarchical pattern: entity.all → lists() → list(filters)
- Migrated existing Claude Code devcontainer to Docker Compose-based setup
- Used Python 3.12-slim with Node.js 20 for Claude Code support
- Manual shadcn/ui component implementation when CLI unavailable (no internet access)
- Configured import-linter with forbidden/layers/independence contracts
- Used Docker secrets for encryption key (not env vars)
- Frozen dataclass with slots for Money value object (immutability + performance)
- 4 decimal places for Money precision (handles exchange rate calculations)
- TypeID-based entity IDs with UUID7 (time-sortable, URL-safe)
- Protocol-based ports instead of ABC (structural subtyping, Pythonic)
- Hypothesis profiles: ci (200 examples), dev (50 examples) for test speed vs thoroughness tradeoff
- Docker secrets primary key source with env fallback for encryption
- Nonce prepended to ciphertext for self-contained encrypted values
- Environment-based logging: ConsoleRenderer (dev) vs JSONRenderer (prod)
- FastAPI lifespan context manager for startup/shutdown lifecycle
- String(36) for entity IDs to accommodate TypeID prefix format
- Partial index on outbox.processed_at for efficient unprocessed event polling
- Separate sync/async session factories for migrations vs API
- Use postgres:5432 hostname in devcontainer (not localhost) for database connections
- TEST_DATABASE_URL environment variable for test database configuration
- DATABASE_URL_SYNC for synchronous Alembic migrations (avoid asyncpg in sync context)
- Removed overly strict adapter independence contract (API is composition root)
- Session-scoped database setup with per-test transactional rollback for integration tests
- Single Account class with type discriminator (not subclasses per account type)
- Account aggregate eq=False (identity by ID, not field comparison)
- Explicit mutation methods with event emission (not frozen dataclass)
- RewardsBalance for rewards accounts (tracks points/miles with unit, not monetary value)
- StrEnum with auto() for type-safe string enums (JSON-friendly, direct comparison)
- Domain events use default values for fields to handle dataclass inheritance
- SQLAlchemy composite() for value object ORM mapping (Money, InstitutionDetails, RewardsBalance)
- Composite factory functions handle nullable composites (return None when all columns NULL)
- Lazy repository initialization via UnitOfWork properties
- AccountError dataclass for explicit failure handling (not exceptions for expected failures)
- Application service owns transaction boundaries (with self._uow context manager)
- Events collected from aggregate and cleared before commit
- API versioning with /api/v1 prefix for accounts router
- Placeholder user ID for development until Phase 4 auth
- Account number masking - show only last 4 digits in responses
- Sync database operations for Phase 2 (async FastAPI routes with sync service/repository layer using psycopg2, full async migration deferred to Phase 4)
- Smart DATABASE_URL handling - prefers DATABASE_URL_SYNC when DATABASE_URL contains asyncpg
- Signed amounts for SplitLine (positive=inflow, negative=outflow)
- Transfer splits must be negative (outgoing from source account)
- Payee normalized_name for case-insensitive matching
- Payee usage tracking (last_used_at, usage_count) for autocomplete relevance
- Always-split transaction model (every transaction has 1+ split lines)
- Mirror transactions for transfers (source owns, mirror auto-created)
- Two-level category hierarchy (parent/child categories)
- System categories protected from modification/deletion (e.g., Uncategorized)
- Date type (not DateTime) for effective_date and posted_date
- TSVECTOR with GIN index for full-text search on transactions
- CASCADE delete on split_lines when transaction deleted
- Transaction.splits and amount excluded from mapper, handled in repository
- SplitLine not mapped directly (frozen dataclass with Money)
- Full-text search via PostgreSQL TSVECTOR/GIN index
- CategoryError/TransactionError dataclasses for explicit failures (matches AccountError pattern)
- Mirror sync handled in service layer via _sync_mirrors_for_split_update
- Transaction.update_amount method for mirror amount sync
- Shared dependencies for services in dependencies.py (reusable across routes)
- UpdateTransactionRequest supports optional splits/amount for full financial updates
- SplitId follows exact pattern of other entity IDs (frozen dataclass, generate, from_string, prefix "split")
- SplitLine.id is required first field, .create() factory generates ID
- Transaction.source_split_id links mirror transactions to their source splits
- CategoryType StrEnum for income/expense classification (default EXPENSE)
- API accepts category_type in CreateCategoryRequest with Pydantic pattern validation
- SplitIdType custom TypeDecorator for ORM mapping of source_split_id
- TypeIDException handler returns INVALID_ID_FORMAT code with 400 status
- Empty string validators use Pydantic field_validator (returns 422)
- PATCH endpoint preserves split IDs when provided in request (new splits get generated IDs)
- TransactionResponse includes source_split_id field for mirror linkage
- PATCH rejects splits with neither category_id nor transfer_account_id (API validation, domain allows)
- PATCH validates provided split IDs exist on transaction before update
- User events are standalone frozen dataclasses (not inheriting DomainEvent base)
- User.collect_events() pattern (copy-then-clear) for event collection
- Email normalization in domain layer (lowercase + strip in User.create())
- verify_email() is idempotent (no-op on already-verified user)
- HouseholdId uses "hh_" prefix in TypeID pattern
- PyJWT over python-jose (abandoned, CVE-2025-61152)
- pwdlib with Argon2 over passlib (deprecated, breaks Python 3.13+)
- itsdangerous for email verification tokens (no DB lookup, signed+timestamped)
- Explicit algorithm list in jwt.decode() to prevent algorithm confusion attacks
- JWT_SECRET from os.environ with fallback default for development
- Required claims (exp, sub, household_id) enforced in JWT decode
- Default household ID is well-known constant hh_00000000000000000000000000 (valid TypeID)
- Circular FK bootstrap: create households.owner_id nullable, populate, then add NOT NULL
- All user-owned data tables (accounts, transactions, categories, payees) have household_id FK
- HouseholdIdType TypeDecorator for ORM mapping of HouseholdId
- Household bootstrap: create with placeholder owner_id, update after user creation
- login() returns same INVALID_CREDENTIALS for bad email and bad password (prevent enumeration)
- EMAIL_NOT_VERIFIED is separate error code (user can take action)
- verify_email() validates token stateless first, then DB lookup (no unnecessary queries)
- Separate port files per entity (user_repository.py, household_repository.py) following existing project pattern
- RefreshTokenRepository uses SQLAlchemy Core (not ORM) for infrastructure records
- RefreshTokenRepository typed as Any in UoW port (domain should not import adapter types)
- User._events excluded from ORM mapping, re-initialized in repository after load
- Cookie secure flag environment-aware (production=True, dev/test=False) for TestClient compatibility
- Auth routes at /auth prefix (no /api/v1) since auth is cross-cutting infrastructure
- UnitOfWork commit skips non-DomainEvent protocol events (UserRegistered is standalone dataclass)
- Registration always returns 202 with generic user_id on duplicate email (enumeration protection)
- OAuth2 login via OAuth2PasswordRequestForm, refresh via HttpOnly cookie at /auth/refresh path
- CurrentUser frozen dataclass with user_id + household_id injected from JWT
- All domain model factory methods accept optional household_id with fallback to well-known default
- Cross-household access returns 404 (not 403) to prevent resource probing
- Routes extract both user_id and household_id from CurrentUser JWT claims
- Removed placeholder get_current_user_id; all routes use real JWT auth
- Auth fixture chain per test file (not shared conftest) for test module independence
- household_id must be threaded through all service layers to domain entity creation (category, transaction, payee)
- CLAUDE.md for project-wide rules (auto-loaded by Claude Code, always visible)
- Chokepoint testing: verify migrations against real DB, smoke test endpoints against running service, never rely solely on integration tests
- Alembic autogenerate: import tables.py in env.py to register Table objects with metadata
- user_module_prefix="types." for clean TypeDecorator rendering in migrations
- compare_type=True for thorough drift detection during autogenerate
- All migrations autogenerated from tables.py metadata (single source of truth)
- Drift detection test guards schema parity between metadata.create_all and alembic upgrade head
- compare_type=True in MigrationContext for thorough type drift detection
- Three-level autogenerate-first documentation: CLAUDE.md, skill file, CHECKPOINTS.md
- UserProfileResponse includes created_at for "member since" display
- is_owner derived from user.role == "owner" (not stored on household)
- CurrentUserDep type alias for JWT-authenticated endpoints
- Nested Pydantic response schemas with from_domain classmethod
- Event bus uses dict[type, list[Callable]] for handler registry (Cosmic Python pattern)
- Handlers called synchronously; async work delegated to job queue
- Exception in handler re-raised for fail-fast in development
- Separate postgres-jobs database on port 5433 for job queue isolation
- UoW publishes events AFTER commit succeeds (RESEARCH.md Pitfall 1)
- JOB_QUEUE_ENABLED env var for graceful degradation when job db unavailable
- Procrastinate job queue with PsycopgConnector for async jobs
- Event handlers registered in lifespan via register_all_handlers()
- Job queue worker runs in same process as API via lifespan
- Direct SQL queries via psql for job queue operations (maximum visibility)
- scripts/jobs/ directory for operational scripts
- docs/runbooks/ directory for operational documentation
- MJML via npm devDependency (not Python package), invoked via npx
- Mailpit always-on Docker Compose service (not optional profile)
- App starts even if SMTP unavailable (mailpit condition: service_started)
- No SMTP_USER/SMTP_PASSWORD for Mailpit (accepts any auth in dev)
- Makefile for non-Python build tooling (build-emails target)
- Jinja2 for email template rendering (runtime variable substitution in compiled HTML)
- FileSystemLoader with StrictUndefined for template safety (catches missing variables)
- EmailService Protocol in domain/ports with SmtpEmailAdapter in adapters/email
- Default SMTP_PORT 1025 for Mailpit dev server, use_tls=False
- Lazy is_available() with cached result for SMTP connectivity checks
- EmailDeliveryError wraps both SMTPException and OSError
- Email PII masking: first 3 chars + *** for log output
- Handler catches defer exceptions for graceful degradation (email is side effect, not critical path)
- 48-hour token expiry to match email template promise
- EmailDeliveryError added to job retry_exceptions for transient SMTP failures
- Lazy import of send_verification_email inside handler to avoid module-level job queue initialization
- Async event bus with mixed sync/async handler support via inspect.iscoroutinefunction
- UoW context manager stays sync, only commit() is async
- Read-only service methods and routes stay sync for thread pool execution
- asyncio.run() in sync tests for async function calls (no pytest-asyncio dependency)
- Manual Nx setup (no `nx init`) for clean integration with existing Python+Node hybrid project
- Nx project.json discovery (not npm workspaces) for monorepo project registration
- Empty Nx project targets -- Phase 8 adds React/Tailwind build configuration
- Backend moved to apps/api/ via git mv (preserves history), editable install via hatch packages=['apps/api/src']
- Root pyproject.toml kept as regular project (not uv workspace) to avoid typeid-python Rust build in offline env
- Nx targets use .venv/bin/ paths and {workspaceRoot} cwd for Python tool execution
- alembic.ini: prepend_sys_path includes both . and apps/api for import resolution
- Domain layer extracted to libs/domain/domain/ as standalone shared library (imports use domain.* not src.domain.*)
- Editable install: hatch packages=['apps/api/src', 'libs/domain/domain'] for both src and domain importability
- uv pip install -e . --no-deps to avoid typeid-python Rust rebuild (use --no-deps flag always)
- pytest --import-mode=importlib for monorepo with multiple test directories
- import-linter root_packages=['src', 'domain'] for cross-package architecture enforcement
- CLAUDE.md documents monorepo structure, import conventions, Nx commands, future phase notes
- ROADMAP.md Phase 7 requirements: descriptive label (not ARCH-06/ARCH-07 which belong to Phase 8/10)
- Per-project pyrightconfig.json in Nx monorepo (each project has own strict config, pyright auto-discovers)
- from __future__ import annotations + concrete return types for frozen dataclass arithmetic (Self requires cls())
- File-level pyright pragma for untyped third-party libraries (entity_id.py for typeid)
- Typed default_factory: lambda: list[T]() for pyright strict (bare list infers list[Unknown])
- Rename DomainException to DomainError (N818 naming convention)
- Per-project pyrightconfig.json includes tests (catches type errors in test code too)
- File-level pyright pragmas for SQLAlchemy-heavy modules (tables.py, types.py) where patterns are too pervasive for per-line ignores
- pyrightconfig.json executionEnvironments to relax mock-related rules (reportUnknownMemberType etc.) in tests/ directory
- Explicit re-export pattern (X as X) in __init__.py for pyright strict re-export detection
- NoReturn annotation on error handlers that always raise (enables type narrowing in callers)
- Per-file-ignores for ARG001/ARG002 in routes, persistence, and tests (framework-required unused params)
- noqa: PT012 for multi-statement pytest.raises where IntegrityError can occur on either execute or commit
- TYPE_CHECKING block for runtime-unused imports when __future__ annotations enabled
- datetime.now(UTC).date() as standard pattern for timezone-aware date creation
- Absolute imports only in src/ (no relative parent imports)
- Coverage targets separate from test targets (npx nx coverage vs npx nx test)
- Terminal-only coverage output (--cov-report=term-missing), no HTML artifacts
- Branch coverage enabled (--cov-branch) for finance app signal
- CI uses nx affected (not run-many) with nrwl/nx-set-shas@v4 for SHA resolution
- Two CI jobs: quality (lint/typecheck/format/import-linter) and test (with postgres)
- npm ci for deterministic CI builds (not npm install)
- fetch-depth: 0 for nx affected git history
- Per-project format Nx targets (ruff format --check) for nx affected execution
- import-linter documented as workspace-scoped (validates cross-project boundaries)
- targetDefaults cache includes test, lint, typecheck, and format for Nx caching
- TypedDict for structured dict returns with distinct key types (eliminates type: ignore[assignment])
- Remove tests that verify language mechanics already enforced by static analysis (frozen dataclass field assignment)
- pnpm as package manager for monorepo (replaces npm, better dependency resolution)
- pnpm workspace config in pnpm-workspace.yaml (apps/*, libs/*)
- shamefully-hoist=true in .npmrc for legacy package compatibility
- pnpm/action-setup@v4 in GitHub Actions for reproducible CI builds
- shadcn CLI with pnpm wrapper script (/tmp/bin/pnpm calling npx pnpm) for component generation
- radix-ui meta-package (not individual @radix-ui/* packages) as official CLI pattern
- Playwright uses system Chromium at /usr/bin/chromium (no bundled browser download)
- Container-safe browser args: --no-sandbox, --disable-gpu, --disable-dev-shm-usage
- Minimal SVG favicon in public/ to prevent console 404 errors in e2e tests
- OpenAPI-first type generation (backend FastAPI spec drives frontend types via openapi-typescript)
- Python script extracts OpenAPI JSON from create_app().openapi() without server startup
- Nx generate-api-types target for one-command type regeneration after API changes
- npx pnpm pattern for pnpm access in environments without global install

### Pending Todos

None.

### Blockers/Concerns

None.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Add chokepoint testing guardrails (CLAUDE.md + GSD agent updates) | 2026-02-05 | ff9f765 | [001-add-chokepoint-testing-guardrails](./quick/001-add-chokepoint-testing-guardrails/) |
| 002 | Split phase 4.3 into event publishing and email phases | 2026-02-06 | ee20011 | [002-split-phase-4-3-into-event-and-email-phases](./quick/002-split-phase-4-3-into-event-and-email-phases/) |

## Session Continuity

Last session: 2026-02-11
Stopped at: Phase 15 complete (8/8 plans, verified 8/8 must-haves)
Resume file: None
Next action: Plan Phase 16 (Error Handling Patterns) or user-directed next step

## Roadmap Evolution

- Phase 3.1 inserted after Phase 3: Split Identity & Validation Fixes (URGENT)
- Phase 3.2 inserted after Phase 3.1: Add Missing PATCH Test Cases (test coverage gaps from 03.1-CONTEXT.md)
  - Plan 01: PATCH Split Modifications (M1-M6) - COMPLETE
  - Plan 02: Split Addition/Removal - COMPLETE
  - Plan 03: Validation Errors - COMPLETE
- Phase 4.2 inserted after Phase 4.1: Current User Metadata Endpoint - Add /auth/me endpoint returning authenticated user profile (INSERTED)
- Phase 4.3 split into Phase 5 (Domain Event Publishing) and Phase 6 (Transactional Email Infrastructure), all subsequent phases renumbered +2

## Phase 1 Milestone

**Phase 1: Foundation - COMPLETE**

All success criteria met:
1. Developer can open project in devcontainer and run tests with single command
2. Domain layer has zero infrastructure imports (verified by lint-imports)
3. Money arithmetic without precision loss (verified by property tests)
4. Database schema with migrations applies to fresh database
5. Security infrastructure encrypts sensitive fields (verified by integration tests)

Ready for Phase 2: Account Domain

## Phase 2 Milestone

**Phase 2: Account Domain - COMPLETE**

All success criteria met:
1. User can create checking, savings, credit card, loan, brokerage, IRA, and rewards accounts with starting balances
2. User can edit account name and properties after creation
3. User can delete an account (system prevents deletion if transactions exist)
4. User can view current balance for each account
5. Historical balance tracking ready (balance = opening_balance + transactions, Phase 3)

Ready for Phase 3: Transaction Domain

## Phase 3 Milestone

**Phase 3: Transaction Domain - COMPLETE**

All success criteria met:
1. User can create, edit, and delete transactions with date, amount, payee, category, and account
2. User can split a transaction across multiple categories with specific amounts
3. User can record a transfer between two accounts as a single transaction that affects both balances
4. (DEFERRED) User can attach receipt files to transactions
5. User can search and filter transactions by payee, category, amount, date, or account

Plans completed (7 of 7):
- 03-01: Transaction Domain Primitives (enums, SplitLine, Payee, events)
- 03-02: Transaction Aggregate and Category entity
- 03-03: Database tables and Alembic migration
- 03-04: ORM mappers and repository implementations
- 03-05: Transaction and Category application services
- 03-06: REST API endpoints
- 03-07: Integration tests and UAT verification (28 tests)

Ready for Phase 3.1: Split Identity & Validation Fixes

## Phase 3.1 Milestone

**Phase 3.1: Split Identity & Validation Fixes - COMPLETE**

All success criteria met:
1. SplitLine has unique ID; PATCH can update specific splits by ID
2. Mirror transactions link to source split via source_split_id
3. Invalid account/category IDs return 400 (not 500)
4. Empty strings return 422 (Pydantic validation)

Plans completed (4 of 4):
- 03.1-01: SplitLine Identity (SplitId, create() factory, source_split_id)
- 03.1-02: CategoryType Vertical Slice (enum, migration, API, 7 tests)
- 03.1-03: Split Identity Persistence (migration 005, repository, exception handlers)
- 03.1-04: Integration Tests (9 unit + 9 integration, fixed PATCH ID preservation)

Ready for Phase 3.2: Add Missing PATCH Test Cases

## Phase 3.2 Milestone

**Phase 3.2: Add Missing PATCH Test Cases - COMPLETE**

All success criteria met:
1. TestPatchSplitModifications with M1-M6 tests (amount change, mirror sync, category change, transfer destination, category-to-transfer, transfer-to-category)
2. TestPatchSplitAddRemove with split addition/removal tests
3. TestPatchValidationErrors with validation tests (invalid split ID, uncategorized splits, both category and transfer, empty strings)

Plans completed (3 of 3):
- 03.2-01: PATCH Split Modifications (M1-M6) - 6 tests
- 03.2-02: Split Addition/Removal - 6 tests
- 03.2-03: Validation Errors - 6 tests + 2 bug fixes

Total new tests: 21 (55 total transaction API tests)
Bugs fixed: 2 (uncategorized splits validation, non-existent split ID validation)

Ready for Phase 4: Authentication Infrastructure

## Phase 4 Milestone

**Phase 4: Authentication Infrastructure - COMPLETE**

All success criteria met:
1. User can register with email/password and verify email via signed token
2. User can login and receive JWT access token + HttpOnly refresh cookie
3. All API endpoints require valid JWT authentication
4. Users can only access data within their own household (cross-household returns 404)
5. All 111 API integration tests pass with real JWT auth flow (24 account + 55 transaction + 17 category + 15 auth)

Plans completed (8 of 8):
- 04-01: User Domain Model (User entity, events, password hashing with Argon2)
- 04-02: JWT Token Infrastructure (PyJWT access tokens, itsdangerous verification tokens)
- 04-03: Household & User Persistence (migration 006, ORM mappers, repositories)
- 04-04: Auth Service (register, login, verify_email, refresh with token rotation)
- 04-05: Auth API Endpoints (register, token, verify, refresh routes)
- 04-06: Auth Integration Tests (15 tests covering full auth flow)
- 04-07: Route Protection & Household Scoping (JWT middleware, CurrentUser injection, household_id FK on all tables)
- 04-08: Update Integration Tests for Auth (96 tests migrated to real auth, 2 household isolation tests, household_id bug fix)

Key stats:
- 407 total tests passing (152 integration + 255 unit)
- 8 plans executed across 4 dependency waves
- 1 critical bug fixed (household_id not threaded through category/transaction services)
- Verification: 5/5 success criteria confirmed

Ready for Phase 7: Nx Monorepo Restructure

## Phase 4.1 Milestone

**Phase 4.1: Test Schema Parity - COMPLETE**

All success criteria met:
1. Single autogenerated migration file exists in alembic/versions/
2. No hand-written migration files remain
3. alembic check confirms zero drift between tables.py metadata and migration chain
4. All 407 existing tests pass
5. Service starts and responds to API requests

Plans completed (2 of 2):
- 04.1-01: Fix Alembic Config and Replace Migrations
- 04.1-02: Drift Detection Test and Workflow Documentation

Key stats:
- 408 total tests passing (407 existing + 1 drift detection)
- 7 hand-written migrations replaced with 1 autogenerated migration
- Schema parity between integration tests and production established
- Drift detection test guards against future schema drift
- Autogenerate-first workflow documented at 3 levels (CLAUDE.md, skill file, CHECKPOINTS.md)

Ready for Phase 4.2: Current User Metadata Endpoint

## Phase 4.2 Milestone

**Phase 4.2: Current User Metadata Endpoint - COMPLETE**

All success criteria met:
1. GET /auth/me with valid JWT returns user profile (user_id, email, display_name, email_verified, created_at)
2. GET /auth/me response includes nested household object with id, name, is_owner
3. GET /auth/me without JWT returns 401 Unauthorized
4. Response does not leak sensitive fields (password_hash not in response)

Plans completed (1 of 1):
- 04.2-01: GET /auth/me endpoint with UserProfileResponse schema and integration tests

Key stats:
- 414 total tests passing (408 existing + 6 new)
- Service smoke tested per CHECKPOINTS.md
- is_owner flag ready for Phase 25 (Multi-User Households)

Ready for Phase 5: Domain Event Publishing

## Phase 5 Milestone

**Phase 5: Domain Event Publishing - COMPLETE**

All success criteria met:
1. Domain events published after aggregate changes commit
2. Event handlers can enqueue async jobs for side effects
3. Job queue worker processes jobs with retry on failure
4. Operators can manage job queue via CLI scripts and runbook

Plans completed (3 of 3):
- 05-01: Event Bus Infrastructure (in-memory bus with dict registry, Cosmic Python pattern)
- 05-02: Job Queue Integration (Procrastinate with separate postgres-jobs database)
- 05-03: Operations Tooling (7 scripts, 300-line runbook)

Key stats:
- 432 total tests passing (all existing tests)
- Separate jobs database on port 5433 for isolation
- JOB_QUEUE_ENABLED env var for graceful degradation
- Comprehensive runbook with monitoring queries and emergency procedures

Ready for Phase 6: Transactional Email Infrastructure

## Phase 6 Milestone

**Phase 6: Transactional Email Infrastructure - COMPLETE**

All success criteria met:
1. MJML email templates compiled to HTML with Jinja2 rendering
2. SmtpEmailAdapter with Mailpit dev server for local email testing
3. Event handler enqueues verification email job via Procrastinate
4. Full async await chain: route -> service -> commit -> publish_all -> handler -> defer_async
5. Integration tests and E2E verification of complete email flow
6. 444 total tests passing, service smoke tested

Plans completed (5 of 5):
- 06-01: MJML Email Templates and Rendering (verification email template, Jinja2 rendering)
- 06-02: Email Service Protocol and SMTP Adapter (SmtpEmailAdapter, Mailpit config)
- 06-03: Event Handler and Job Queue Email Integration (send_verification_email job, handler wiring)
- 06-04: Integration Tests and E2E Verification (MockEmailAdapter, 11 tests, E2E Mailpit flow)
- 06-05: Async Event Bus, UoW, Services, Routes (full async conversion, eliminate create_task workaround)

Key stats:
- 444 total tests passing (444 existing, tests updated for async)
- Full async publish chain eliminates fire-and-forget create_task workaround
- 30 service write methods converted to async across 4 service files
- 17 files modified in 06-05 (largest plan in phase)
- Proper error handling: defer_async failures caught by handler try/except

Ready for Phase 7: Nx Monorepo Restructure

## Phase 7 Milestone

**Phase 7: Nx Monorepo Restructure - COMPLETE**

All success criteria met:
1. Project uses Nx monorepo structure (Nx 22.4.5, 4 projects)
2. Backend at apps/api/ with serve, test, lint Nx targets
3. Frontend scaffold at apps/web/ (empty, ready for Phase 8)
4. Libraries at libs/domain/ (shared domain) and libs/ui/ (future shadcn/ui)
5. All 444 existing tests pass after restructure (252 API + 192 domain)
6. Nx commands work for all projects (test, lint, serve)

Plans completed (4 of 4):
- 07-01: Nx Workspace Init (nx.json, apps/web, libs/ui scaffolds)
- 07-02: Backend as Nx Project (git mv to apps/api/, Nx project.json, config updates)
- 07-03: Domain Layer Extraction (libs/domain/domain/, import rewrite, Nx project registration)
- 07-04: CLAUDE.md Update & Final Verification (docs, E2E smoke test)

Key stats:
- 444 total tests passing (252 API + 192 domain)
- Nx 22.4.5, 4 projects: api, domain, web, ui
- Hatch packages for Python editable install (not uv workspaces)
- import-linter: 2 contracts kept (domain isolation + hexagonal layers)
- Git history preserved across all file moves
- Service operational, alembic migrations clean, zero drift

Ready for Phase 8: CI & Code Quality

## Phase 8 Milestone

**Phase 8: CI & Code Quality - COMPLETE**

All success criteria met:
1. GitHub Actions CI configured with all quality gates blocking (lint, typecheck, test, format, import-linter)
2. All pyright strict errors resolved — domain: 52→0, api: 2067→0
3. All ruff lint errors resolved — domain: 33→0, api: 173→0
4. Code coverage Nx targets configured (api: 81%, domain: 48%)
5. import-linter passes (2/2 contracts kept)

Plans completed (4 of 4):
- 08-01: Tooling config + domain fixes (pyrightconfig.json, py.typed, ruff config, format)
- 08-02: API pyright strict errors (2067→0 with justified type: ignore annotations)
- 08-03: API ruff lint errors (173→0, absolute imports, timezone-aware datetime)
- 08-04: Coverage targets + CI restructure (nx affected, uv+npm caching, blocking gates)

Key stats:
- 444 total tests passing (252 API + 192 domain)
- All quality gates pass locally: lint, typecheck, test, format, import-linter
- CI uses nx affected with nrwl/nx-set-shas@v4 for PR-scoped execution
- Verification: 5/5 success criteria confirmed

Ready for Phase 9: Frontend Infrastructure

## Phase 8 Milestone

**Phase 8: CI & Code Quality - COMPLETE**

All success criteria met:
1. Pyright strict mode with zero errors across api and domain projects
2. Ruff lint with zero errors across api and domain projects
3. Ruff format check passes (all files formatted)
4. import-linter passes (2/2 architecture contracts kept)
5. CI pipeline with nx affected, dependency caching, and all blocking quality gates
6. Coverage targets for api (81%) and domain (48%) projects

Plans completed (4 of 4):
- 08-01: Tooling and Domain Cleanup (pyrightconfig.json, py.typed, ruff config, domain 0 errors)
- 08-02: Fix API Pyright Errors (2067 -> 0 strict errors across 42 files)
- 08-03: Fix API Ruff Lint Errors (173 -> 0 lint errors across 40 files)
- 08-04: CI Pipeline Configuration (nx affected, caching, coverage targets, all blocking gates)

Key stats:
- 444 total tests passing (252 API + 192 domain)
- Zero pyright strict errors, zero ruff lint errors
- CI: 2 parallel jobs (quality + test), nx affected for efficiency
- Coverage baseline: API 81%, Domain 48%
- 10 formatting fixes in 08-04 for clean format check gate

Ready for next phase in roadmap

## Phase 9 Milestone

**Phase 9: Type Safety & Test Cleanup - COMPLETE**

All success criteria met:
1. get_category_tree returns a CategoryTree TypedDict with distinct types per key
2. categories.py has zero type: ignore comments for tree access
3. No redundant immutability tests exist for frozen dataclasses

Plans completed (1 of 1):
- 09-01: CategoryTree TypedDict + remove redundant immutability tests

Key stats:
- 437 total tests passing (252 API + 185 domain, -7 redundant tests removed)
- CategoryTree TypedDict eliminates 2 type: ignore[assignment] comments
- 7 frozen dataclass immutability tests removed (pyright strict covers these)
- All quality gates pass: typecheck, test, lint, format

Ready for Phase 10: Value Object ORM Mapping

## Phase 10 Milestone

**Phase 10: Value Object ORM Mapping - COMPLETE**

All success criteria met:
1. SQLAlchemy composite() maps Money, InstitutionDetails, RewardsBalance to flat DB columns
2. _decompose_value_objects before_flush handler is removed
3. Manual value object reconstruction in AccountRepository is removed
4. 16 type: ignore[attr-defined] comments eliminated from mappers.py
5. All 437 existing tests pass

Plans completed (1 of 1):
- 10-01: SQLAlchemy composite() for Money, InstitutionDetails, RewardsBalance

Key stats:
- 437 total tests passing (252 API + 185 domain)
- 153 lines of manual mapping code eliminated
- Factory functions handle nullable composites (return None when all columns NULL)
- Verification: 5/5 must-haves confirmed

Ready for Phase 11: Domain Test Coverage

## Phase 12 Milestone

**Phase 12: Frontend Infrastructure - COMPLETE**

All success criteria met:
1. React app runs with Tailwind CSS v4 (Vite 7, React 19, CSS-first @theme)
2. shadcn/ui component library integrated and working (Button, Card, Input, Label + cn utility)
3. Playwright configured for E2E UI testing (chromium-only, local-only)
4. Basic smoke test passes (app renders without errors, 2 Vitest + 2 Playwright tests)

Plans completed (6 of 6):
- 12-01: pnpm migration + CI update (packageManager field, onlyBuiltDependencies)
- 12-02: React+Vite scaffold + FastAPI CORS (React 19, Vite 7, port 5173)
- 12-03: Tailwind CSS v4 + ESLint + Prettier (dark mode, Fontsource fonts, flat config)
- 12-04: libs/ui + shadcn/ui + app shell (internal package, sidebar layout)
- 12-05: Vitest + Playwright + Nx targets (test, lint, typecheck, format, e2e)
- 12-06: shadcn/ui CLI components + Playwright system Chromium (gap closure)

Key stats:
- 63 total plans completed across all phases
- All quality gates pass: npx nx test/lint/typecheck/format web
- Verification: 28/28 must-haves confirmed (22 from 12-05 + 6 from 12-06)
- Frontend stack: React 19 + Vite 7 + Tailwind CSS v4 + official shadcn/ui + Vitest + Playwright
- Package manager: pnpm with workspace configuration
- Dark mode: class-based with localStorage persistence
- Self-hosted fonts: Inter (UI) + JetBrains Mono (financial figures)
- Components: Official CLI-generated (use `shadcn diff` to check for updates)
- E2E: System Chromium at /usr/bin/chromium (~180 MB saved per container rebuild)

Ready for Phase 12.1: UI Acceptance Testing Framework

## Phase 13 Milestone

**Phase 13: Login UI - COMPLETE**

All success criteria met:
1. Login page with form (email/password, remember me, validation)
2. Successful login stores JWT token and redirects to dashboard
3. Session persists across browser refresh (cookie-based refresh)
4. User can log out from dashboard (UserMenu dropdown)
5. Unauthenticated users redirected to login (protected route guards)

Plans completed (6 of 6):
- 13-01: Backend cookie fixes (samesite=lax, remember_me) + Axios client + auth types
- 13-02: shadcn/ui components (Form, Checkbox, DropdownMenu, Avatar)
- 13-03: AuthContext provider + useAuth hook + routing + ProtectedRoute
- 13-04: Login page + Registration page (forms, validation, password toggle)
- 13-05: Email verification page + UserMenu (logout) + Dashboard shell
- 13-06: Unit tests + E2E verification (4 bug fixes during E2E)

Key stats:
- 68 total plans completed across all phases
- 17 unit tests for auth components and context
- 4 bugs fixed during E2E verification (redirect loop, stuck loading, form reload, post-login nav)
- Full login-to-logout cycle verified via Chrome DevTools
- Verification: 5/5 success criteria confirmed

Ready for Phase 14: Frontend API & Routing

## Phase 14 Milestone

**Phase 14: Frontend API & Routing - COMPLETE**

All success criteria met:
1. TanStack Query configured for API state management
2. TanStack Router loaders use queryOptions + ensureQueryData for instant navigation
3. Type-safe API client generated from OpenAPI spec
4. Authentication token automatically included in API requests
5. API error responses handled consistently
6. Playwright e2e smoke tests updated for auth

Plans completed (4 of 4):
- 14-01: OpenAPI type generation + TanStack Query install
- 14-02: TanStack Query setup + type-safe API client + queryOptions + route loaders
- 14-03: MSW test infrastructure + API client/error tests
- 14-04: Playwright e2e auth fixtures + smoke tests

Key stats:
- 72 total plans completed across all phases
- OpenAPI type generation pipeline (Python script -> openapi-typescript -> api-types.generated.ts)
- MSW v2 for API mocking in Vitest tests
- Playwright auth fixture chain (register -> Mailpit verify -> login -> storageState)

Ready for Phase 15: API Integration Validation

## Phase 15 Milestone

**Phase 15: API Integration Validation - COMPLETE**

All success criteria met:
1. User can create an account via 4-step wizard UI (all 7 types)
2. User can update an account via edit wizard (pre-filled, type locked)
3. User can delete an account via type-to-confirm dialog
4. Sidebar shows accounts grouped by type (Cash, Credit, Loans, Investments, Rewards) with subtotals
5. E2E tests cover account CRUD flows
6. Chrome DevTools MCP used to automate UAT (6/6 flows passed)

Plans completed (8 of 8):
- 15-01: Dependencies, shadcn/ui components, API client completion
- 15-02: Empty state welcome screen + account sidebar with grouping
- 15-03: Account wizard modal (4-step) + delete confirmation dialog
- 15-04: TanStack Query mutation hooks + DashboardPage rewire + routing
- 15-05: useAccountWizard hook (multi-step form state)
- 15-06: Vitest unit/component tests (50 new tests, 88 total)
- 15-07: Playwright E2E tests for account CRUD flows
- 15-08: UAT via Chrome DevTools MCP (6/6 flows passed)

Key stats:
- 79 total plans completed across all phases
- 50 new Vitest tests (88 total web tests)
- 3 Playwright E2E tests for account CRUD
- 5 shadcn/ui components added (Dialog, Select, RadioGroup, Separator, Badge)
- Full account CRUD: 7 account types, type-specific fields, currency formatting
- Verification: 8/8 must-haves confirmed

Ready for Phase 16: Error Handling Patterns
