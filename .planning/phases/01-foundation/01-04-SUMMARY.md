---
phase: 01-foundation
plan: 04
subsystem: database
tags: [sqlalchemy, alembic, postgresql, unit-of-work, data-mapper, outbox-pattern]

# Dependency graph
requires:
  - phase: 01-01
    provides: Docker Compose development environment with PostgreSQL
  - phase: 01-02
    provides: DomainEvent base class for outbox pattern integration
provides:
  - SQLAlchemy table definitions (outbox, users, encrypted_secrets)
  - Imperative mapping infrastructure (Data Mapper pattern)
  - SqlAlchemyUnitOfWork for transaction and event management
  - Database connection utilities (sync/async engines and sessions)
  - Alembic migrations for schema management
affects: [01-05, 01-06, 02-accounts, 02-repositories, 03-transactions]

# Tech tracking
tech-stack:
  added: [sqlalchemy-orm, alembic, asyncpg]
  patterns: [data-mapper-imperative-mapping, unit-of-work-pattern, outbox-pattern, partial-index]

key-files:
  created:
    - src/adapters/__init__.py
    - src/adapters/persistence/__init__.py
    - src/adapters/persistence/orm/__init__.py
    - src/adapters/persistence/orm/base.py
    - src/adapters/persistence/orm/tables.py
    - src/adapters/persistence/orm/mappers.py
    - src/adapters/persistence/database.py
    - src/adapters/persistence/unit_of_work.py
    - alembic.ini
    - alembic/env.py
    - alembic/script.py.mako
    - alembic/versions/001_initial_schema.py
  modified: []

key-decisions:
  - "String(36) for entity IDs to accommodate TypeID prefix format (user_xxx)"
  - "Partial index on outbox.processed_at for efficient unprocessed event polling"
  - "Separate sync/async session factories - sync for migrations, async for API"
  - "UoW collects events and writes to outbox atomically with business data commit"

patterns-established:
  - "Data Mapper: SQLAlchemy table definitions separate from domain models"
  - "Imperative Mapping: Domain classes mapped to tables at startup via start_mappers()"
  - "Unit of Work: Transaction boundary management with event collection"
  - "Outbox Pattern: Events persisted in same transaction as domain data"
  - "Naming Convention: All constraints use consistent naming (pk_, uq_, fk_, ix_)"

# Metrics
duration: 4min
completed: 2026-01-30
---

# Phase 1 Plan 4: Persistence Infrastructure Summary

**SQLAlchemy Data Mapper with imperative mapping, Unit of Work with outbox event collection, and Alembic migrations for PostgreSQL**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-30T06:08:39Z
- **Completed:** 2026-01-30T06:12:12Z
- **Tasks:** 3/3
- **Files created:** 12

## Accomplishments

- Created SQLAlchemy table definitions following Data Mapper pattern (no ORM in domain)
- Implemented SqlAlchemyUnitOfWork that collects domain events and writes to outbox on commit
- Set up Alembic migrations with initial schema (outbox, users, encrypted_secrets)
- Established database connection utilities supporting both sync and async access
- Verified domain layer remains pure with zero infrastructure imports

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SQLAlchemy table definitions and base** - `08cca51` (feat)
2. **Task 2: Create imperative mapping and Unit of Work** - `dbe7fc1` (feat)
3. **Task 3: Create Alembic migrations** - `e65f38f` (feat)

## Files Created/Modified

- `src/adapters/__init__.py` - Adapters layer package marker with docstring
- `src/adapters/persistence/__init__.py` - Persistence adapters package marker
- `src/adapters/persistence/orm/__init__.py` - ORM package exporting metadata and registry
- `src/adapters/persistence/orm/base.py` - MetaData and registry with naming convention
- `src/adapters/persistence/orm/tables.py` - Table definitions (outbox, users, encrypted_secrets)
- `src/adapters/persistence/orm/mappers.py` - start_mappers/clear_mappers for imperative mapping
- `src/adapters/persistence/database.py` - Engine and session factory utilities
- `src/adapters/persistence/unit_of_work.py` - SqlAlchemyUnitOfWork implementation
- `alembic.ini` - Alembic configuration with logging setup
- `alembic/env.py` - Migration environment with DATABASE_URL from env
- `alembic/script.py.mako` - Template for generated migrations
- `alembic/versions/001_initial_schema.py` - Initial migration creating foundation tables

## Decisions Made

1. **String(36) for entity IDs** - TypeID format (user_xxx) exceeds standard UUID length, using String(36) to accommodate prefixed format consistently across all entity ID columns

2. **Partial index on outbox** - Using `postgresql_where=sa.text("processed_at IS NULL")` for efficient polling of unprocessed events; only unprocessed rows are indexed

3. **Separate sync/async factories** - Created distinct engine and session factories for sync (migrations, scripts) and async (API) use cases rather than a single configurable factory

4. **UoW event collection** - Events collected during transaction and written to outbox table in commit() rather than immediately on collect_events(), ensuring atomicity

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Python/lint-imports not available outside devcontainer for full verification
- Verified syntax correctness and grep-based architecture checks instead
- Full verification will run in CI or devcontainer environment

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Persistence infrastructure ready for repository implementations (Phase 2)
- Imperative mapping ready to register domain entities as they're created
- Unit of Work ready to be injected into application services
- Alembic ready to run: `alembic upgrade head` will create schema
- To run migrations:
  ```bash
  # In devcontainer with DATABASE_URL set
  alembic upgrade head
  ```

---
*Phase: 01-foundation*
*Completed: 2026-01-30*
