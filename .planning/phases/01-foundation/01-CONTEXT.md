# Phase 1: Foundation - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the architectural foundation, development environment, and core domain primitives that enforce correctness guarantees for the entire personal finance application. This includes clean architecture scaffolding, DDD patterns implementation, Money value object with precision arithmetic, database schema with migrations, and security infrastructure for field-level encryption.

</domain>

<decisions>
## Implementation Decisions

### Development Environment

**Container & Services:**
- Migrate from existing Claude Code devcontainer baseline
- Expand to use Docker Compose for separate services (app, PostgreSQL, Redis, etc.)
- Services defined in docker-compose.yml for realistic local development

**Testing Framework:**
- pytest for unit and integration tests
- hypothesis for property-based testing (Money arithmetic, value objects)
- Property tests verify correctness guarantees (e.g., Money precision)

**Local Development Experience:**
- Hot reload enabled (uvicorn --reload for FastAPI)
- VS Code debugger fully configured
- Tests can run on save for rapid feedback

**Package Management:**
- uv as Python package manager
- Lockfile support for reproducible builds

**CI/CD:**
- GitHub Actions configured in Phase 1 (now)
- Run tests and linting on every push
- Deployment pipelines added in later phases

**Pre-commit Hooks:**
- Auto-format code before commit
- Run linting checks
- Run type checking
- Full enforcement (format + lint + types)

**Database Initialization:**
- PostgreSQL starts in container
- Manual migration command (developer runs when ready)
- No auto-migration or seed data by default

**UI Testing:**
- Deferred to Phase 4 when web interface is built
- Keep Phase 1 focused on backend foundation

**Environment Variables & Secrets:**
- Docker secrets for configuration management
- Sensitive values handled via Docker Compose secrets

**Logging:**
- Structured JSON logging for production readiness
- Formatted console output for development (human-readable)
- Environment-based configuration (JSON in prod, pretty in dev)

**Documentation:**
- Full documentation from the start
- README with setup and run instructions
- Docstrings on all public APIs
- Architecture documentation

**Database Tools:**
- VS Code PostgreSQL extension for database browsing
- No separate pgAdmin or GUI tools

### Architecture Enforcement

**DDD Tactical Patterns:**
- Full DDD implementation:
  - Entities
  - Value Objects
  - Aggregates
  - Repositories
  - Domain Services
  - Domain Events

**Bounded Contexts:**
- Single bounded context for all domain logic
- Personal finance domain is cohesive enough to start unified

**Aggregate Design:**
- Small aggregates (each guards one consistency boundary)
- Account and Transaction as separate aggregates
- Favor flexibility over large transactional boundaries

**Domain Events:**
- Outbox pattern from the start
- Events saved to database outbox table in same transaction as domain changes
- Background worker reads outbox and handles events
- Guarantees at-least-once delivery
- Sets up infrastructure for Plaid sync, webhooks, notifications in later phases
- NOT event sourcing (events are not the source of truth)
- NOT in-memory only (need reliable delivery for integrations)

**Repository Pattern:**
- One repository per aggregate root
- Repositories expose only aggregate-specific operations
- No generic CRUD repositories

**Architecture Layers:**
- Hexagonal architecture (Domain + Adapters)
- Core domain with ports and adapters pattern
- Clear separation between domain logic and infrastructure

**Unit of Work:**
- Explicit Unit of Work pattern
- Repositories work within UoW context
- UoW manages transaction boundaries

**Business Logic Location:**
- Rich domain models
- Business logic lives in entities and aggregates
- Domain services for multi-aggregate operations
- Application services orchestrate only (thin orchestration layer)

**Entity Identity:**
- Domain-generated UUIDs
- IDs prefixed with entity type for easy identification
- Examples: `acct_xxx`, `txn_xxx`, `user_xxx` (Stripe-style)
- ID is part of domain identity, not infrastructure concern

**Domain/Persistence Mapping:**
- Separate DTO and ORM models from domain models
- Domain models remain pure (no ORM annotations or infrastructure concerns)
- Mappers convert between domain ↔ ORM and domain ↔ API DTOs
- Clean separation, more code but maintains architectural boundaries

**Codebase Structure:**
- Hexagonal package structure:
  - `src/domain/` - core domain logic
  - `src/adapters/persistence/` - database adapters
  - `src/adapters/api/` - API/web adapters
- Ports and adapters organization

### Claude's Discretion

**Code Quality Tools:**
- Choice between ruff+mypy vs black+flake8+mypy
- Claude selects tooling that best enforces code quality

**Clean Architecture Enforcement:**
- Mechanism to prevent domain layer from importing infrastructure
- Options: import linter rules, package structure + linter, or architecture tests
- Claude picks enforcement that prevents violations effectively

**Dependency Injection:**
- Approach: Dependency Injector library, FastAPI native DI, or manual injection
- Claude selects DI strategy that fits clean architecture best

**Value Object Implementation:**
- Choice between frozen dataclasses, Pydantic models, or custom classes
- Claude picks approach that balances immutability and validation needs

**Error Handling Strategy:**
- Mix of domain exceptions and Result types
- Claude determines when to use exceptions vs Result pattern
- Consider: exceptions for exceptional cases, Results for expected failures

**Validation Strategy:**
- Where validation happens: value object constructors, aggregate boundaries, or layered
- Claude designs validation that enforces invariants at right boundaries

</decisions>

<specifics>
## Specific Ideas

- Entity IDs should follow Stripe's pattern with prefixes: `acct_xxx`, `txn_xxx` for easy identification and debugging
- Docker Compose setup should mirror production environment for realistic local development
- Outbox pattern sets foundation for reliable Plaid integration in Phase 6
- Property-based testing with hypothesis specifically for Money arithmetic to verify precision guarantees

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 1 scope (foundation and architecture). UI testing tools deferred to Phase 4 when web interface is built.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-01-29*
