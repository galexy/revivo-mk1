# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-29)

**Core value:** Own your financial data and access it anywhere through any interface - web, API, CLI, or AI. Your data, your tools, no vendor lock-in.
**Current focus:** Phase 4 (Authentication Infrastructure) - COMPLETE

## Current Position

Phase: 4 of 20 (Authentication Infrastructure) - COMPLETE
Plan: 8 of 8 complete (04-01, 04-02, 04-03, 04-04, 04-05, 04-06, 04-07, 04-08)
Status: Phase complete
Last activity: 2026-02-05 - Completed quick/001-PLAN.md (Add Chokepoint Testing Guardrails)

Progress: [██████░░░░] ~40%

## Performance Metrics

**Velocity:**
- Total plans completed: 35
- Average duration: 4.8 min
- Total execution time: 3.38 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 6 | 32 min | 5.3 min |
| 02-account-domain | 6 | 62 min | 10.3 min |
| 03-transaction-domain | 7 | 35 min | 5.0 min |
| 03.1-split-identity-validation-fixes | 4 | 21 min | 5.3 min |
| 03.2-add-missing-patch-test-cases | 3 | 7 min | 2.3 min |
| 04-authentication-infrastructure | 8 | 46 min | 5.8 min |

**Recent Trend:**
- Last 5 plans: 04-04 (4 min), 04-06 (7 min), 04-07 (8 min), 04-08 (9 min), quick-001 (2 min)
- Trend: Phase 4 complete, chokepoint guardrails added

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Migrated existing Claude Code devcontainer to Docker Compose-based setup
- Used Python 3.12-slim with Node.js 20 for Claude Code support
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
- Value object reconstruction in repository layer (not SQLAlchemy composite() mappings)
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

### Pending Todos

None yet.

### Blockers/Concerns

None.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Add chokepoint testing guardrails (CLAUDE.md + GSD agent updates) | 2026-02-05 | ff9f765 | [001-add-chokepoint-testing-guardrails](./quick/001-add-chokepoint-testing-guardrails/) |

## Session Continuity

Last session: 2026-02-05
Stopped at: Completed quick/001-PLAN.md (Add Chokepoint Testing Guardrails)
Resume file: None
Next action: Begin Phase 5 (Nx Monorepo Restructure)

## Roadmap Evolution

- Phase 3.1 inserted after Phase 3: Split Identity & Validation Fixes (URGENT)
- Phase 3.2 inserted after Phase 3.1: Add Missing PATCH Test Cases (test coverage gaps from 03.1-CONTEXT.md)
  - Plan 01: PATCH Split Modifications (M1-M6) - COMPLETE
  - Plan 02: Split Addition/Removal - COMPLETE
  - Plan 03: Validation Errors - COMPLETE
- Phase 4.2 inserted after Phase 4.1: Current User Metadata Endpoint - Add /auth/me endpoint returning authenticated user profile (INSERTED)
- Phase 4.3 inserted after Phase 4.2: Transactional Email Infrastructure - Email domain, SMTP adapter, Mailpit dev env, verification email on registration, mocked emails in integration tests (INSERTED)

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

Ready for Phase 5: Nx Monorepo Restructure
