# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-29)

**Core value:** Own your financial data and access it anywhere through any interface - web, API, CLI, or AI. Your data, your tools, no vendor lock-in.
**Current focus:** Phase 2 - Account Domain (in progress)

## Current Position

Phase: 2 of 10 (Account Domain)
Plan: 6 of 6 in current phase
Status: Complete
Last activity: 2026-01-30 - Completed Phase 2 (Account Domain)

Progress: [███░░░░░░░] ~30%

## Performance Metrics

**Velocity:**
- Total plans completed: 12
- Average duration: 7.8 min
- Total execution time: 1.57 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 6 | 32 min | 5.3 min |
| 02-account-domain | 6 | 62 min | 10.3 min |

**Recent Trend:**
- Last 5 plans: 02-02 (8 min), 02-03 (6 min), 02-04 (3 min), 02-05 (4 min), 02-06 (25 min)
- Trend: Testing and verification phases take longer due to manual verification checkpoints

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

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-01-30
Stopped at: Completed Phase 2 (Account Domain)
Resume file: None

## Phase 1 Milestone

**Phase 1: Foundation - COMPLETE** ✓

All success criteria met:
1. ✓ Developer can open project in devcontainer and run tests with single command
2. ✓ Domain layer has zero infrastructure imports (verified by lint-imports)
3. ✓ Money arithmetic without precision loss (verified by property tests)
4. ✓ Database schema with migrations applies to fresh database
5. ✓ Security infrastructure encrypts sensitive fields (verified by integration tests)

Ready for Phase 2: Account Domain

## Phase 2 Milestone

**Phase 2: Account Domain - COMPLETE** ✓

All success criteria met:
1. ✓ User can create checking, savings, credit card, loan, brokerage, IRA, and rewards accounts with starting balances
2. ✓ User can edit account name and properties after creation
3. ✓ User can delete an account (system prevents deletion if transactions exist)
4. ✓ User can view current balance for each account
5. ✓ Historical balance tracking ready (balance = opening_balance + transactions, Phase 3)

Ready for Phase 3: Transaction Domain
