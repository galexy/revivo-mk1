# Project Research Summary

**Project:** Personal Finance Application
**Domain:** Personal Finance Management / Fintech
**Researched:** 2026-01-29
**Confidence:** HIGH

## Executive Summary

This research validates the technical foundation for a modern personal finance platform targeting "Quicken refugees" — power users frustrated with dated UX in legacy tools and dumbed-down features in modern apps. The market opportunity is clear: provide Quicken-level depth (reconciliation, investment holdings, split transactions) with Monarch-level UX and couples support.

The recommended approach centers on Domain-Driven Design with Clean Architecture (hexagonal/ports & adapters) using Python/FastAPI/PostgreSQL on the backend and React/TypeScript on the frontend. The stack is battle-tested for fintech applications, with particular strength in DDD support: FastAPI's dependency injection enables proper layering, SQLAlchemy 2.0 supports data mapper patterns, and Pydantic handles DTOs cleanly. Critical architectural decisions include implementing double-entry accounting from day one, using Money value objects (never floats), and abstracting Plaid integration behind domain ports.

The primary risk is complexity: DDD adds upfront cost compared to CRUD patterns, and double-entry accounting has a learning curve. However, this investment prevents catastrophic technical debt in financial systems. The research identified five critical pitfalls that must be addressed in Phase 1 (Foundation): floating-point money storage, anemic domain models, insecure credential storage, improper double-entry implementation, and Plaid error handling. Each has been verified through multiple authoritative sources and has specific prevention strategies.

## Key Findings

### Recommended Stack

The pre-selected stack (Python/FastAPI/PostgreSQL/SQLAlchemy backend, React/TypeScript frontend) is well-suited for this domain. Research validated supporting libraries and identified key architectural patterns.

**Core technologies:**
- **Python 3.12+ with FastAPI 0.115+**: Async-native, automatic OpenAPI generation, excellent DI via `Depends` — best-in-class for DDD + Clean Architecture
- **PostgreSQL 16+ with SQLAlchemy 2.0**: ACID compliance critical for financial data, data mapper pattern supports DDD, async support via asyncpg
- **React 18+ with TypeScript 5.5+**: Strong component model, Zustand + TanStack Query recommended over Redux for state management
- **Plaid Python SDK (v29.x)**: Official SDK for bank integration, monthly updates, async support with sandbox environment
- **Decimal (stdlib) + py-money**: Never use floats for money — store as Decimal or integer cents, use Money value object for currency-aware operations

**Key insights from stack research:**
- Zustand + TanStack Query eliminates need for Redux in most cases (simpler, less boilerplate)
- @hey-api/openapi-ts generates type-safe TypeScript clients from FastAPI's OpenAPI spec
- FastAPI's `Depends` is sufficient for request-scoped DI; dependency-injector optional for complex app-wide singletons
- SQLAlchemy's imperative mapping enables strict domain/persistence separation, though pragmatic declarative approach with mappers is also viable
- ARQ (async Redis queue) recommended over Celery for background tasks unless proven enterprise complexity needed

### Expected Features

Personal finance apps in 2026 have clear table stakes established by YNAB, Monarch, Copilot, and Lunch Money. Users expect bank sync, multi-account support, categorization, and basic budgeting. The opportunity lies in adding power-user features modern apps have removed.

**Must have (table stakes):**
- Bank account sync via Plaid — manual entry is a deal-breaker
- Multi-account support (checking, savings, credit cards minimum)
- Transaction categorization with auto-categorization AND manual override
- Split transactions (one payment across multiple categories)
- Transfer detection (link both sides, don't double-count)
- Basic budgeting (category limits, spent vs. remaining)
- Mobile app (iOS minimum, Android expected)
- Search, filter, and basic reports

**Should have (competitive differentiators):**
- Reconciliation workflow (Quicken power feature, rare in modern apps)
- Investment tracking at holdings level (individual stocks, cost basis)
- ESPP/stock option support (very few apps handle well)
- Cash flow forecasting (project balances based on scheduled transactions)
- Multi-user/couples support with shared views ("mine, yours, ours" labeling)
- Custom rules engine (auto-categorize based on user patterns)
- Goals with account association (link savings to specific goal)

**Defer (v2+):**
- AI-powered insights and natural language queries
- Multi-currency full support (complex edge cases)
- Quicken import tool (migration aid)
- API access for power users
- Credit score tracking
- Rewards/points tracking

**Anti-features (explicitly avoid):**
- Real-time everything (creates complexity, users don't need second-by-second updates)
- Heavy gamification (feels patronizing for serious finance management)
- AI auto-budgeting without human confirmation (removes user agency)
- Automatic bill pay (liability risk)
- Bank credential storage (security nightmare)

### Architecture Approach

Hexagonal architecture (ports & adapters) provides the cleanest foundation for multi-interface support (Web UI, REST API, CLI, AI agent). The domain layer must be pure — no framework imports, no database knowledge.

**Major components:**
1. **Domain Layer (core)** — Pure business logic with four bounded contexts:
   - Accounts: Account aggregate, Balance, AccountType value objects
   - Transactions: Transaction aggregate with double-entry model, Money value object, Category
   - Budgeting: Budget aggregate, SpendingLimit, BudgetPeriod
   - Bank Sync: BankConnection aggregate, Plaid abstraction via port interface

2. **Application Layer** — Use cases orchestrate domain objects:
   - One class per use case with single `execute()` method
   - Coordinates transactions, manages persistence boundaries
   - Examples: RecordTransferUseCase, SyncBankAccountUseCase, ReconcileTransactionsUseCase

3. **Infrastructure Layer** — Adapters implement domain/application ports:
   - PostgreSQL repositories with data mappers (domain ↔ persistence translation)
   - Plaid adapter (implements IBankDataProvider port)
   - Background jobs (BullMQ/ARQ for scheduled syncs)
   - OpenTelemetry instrumentation

4. **Interface Layer** — Primary adapters (entry points):
   - REST API (FastAPI controllers, thin, delegate to use cases)
   - Mobile app (iOS/Android)
   - CLI (operations, debugging)
   - AI agent interface (future)

**Critical architectural patterns:**
- **Double-entry accounting model**: Every transaction has balanced debits and credits; transfers are natural, not special cases
- **Money value object**: Immutable, stores as integer cents, enforces currency safety
- **Repository with data mapper**: Domain entities never know about database schema
- **Light CQRS**: Separate query services for read-heavy reports without full event sourcing
- **Plaid via port/adapter**: Domain never knows about Plaid; can swap providers

### Critical Pitfalls

These five pitfalls can cause rewrites or major financial/security issues. Each must be addressed in Phase 1.

1. **Using floating-point for money** — Precision loss leads to penny discrepancies at scale. Prevention: Use Decimal types or integer cents; Money value object with currency awareness. This MUST be established in Phase 1 (Foundation) — retrofitting is catastrophically expensive.

2. **Anemic domain model** — Pushing all logic into services makes invariants impossible to enforce. Prevention: Account entity manages its own balance, Money encapsulates arithmetic, business rules belong in domain entities. Rich domain model from day one.

3. **Insecure credential storage** — Plaid access tokens grant ongoing bank account access. Prevention: Field-level AES-256 encryption, KMS-managed keys, never log tokens, implement rotation policies. Security architecture designed before storing any sensitive data.

4. **Mishandling Plaid item error states** — Bank connections silently break, users discover stale data weeks later. Prevention: Implement webhooks for `PENDING_DISCONNECT`/`PENDING_EXPIRATION`, build "Update Mode" Link flow, monitor `consent_expiration_time`, proactive user alerts.

5. **Not implementing double-entry accounting** — Single-entry makes transfers impossible to model correctly, no built-in balance checking, incomplete audit trails. Prevention: Every transaction has balanced debits/credits, transfers are one transaction with two entries, running balance on every entry.

**Additional moderate pitfalls:**
- N+1 queries on transaction lists (prevention: eager loading, composite indexes)
- Synchronous Plaid calls in request cycle (prevention: background jobs, webhooks)
- No audit logs for balance changes (prevention: log all mutations with before/after values)
- Storing transactions without original bank data (prevention: preserve raw Plaid responses)
- Time-dependent logic without dependency injection (prevention: inject time service)

## Implications for Roadmap

Based on research, suggested phase structure follows dependency order and complexity management:

### Phase 1: Foundation (Domain Model & Core Infrastructure)
**Rationale:** Must establish architectural foundation before building features. Financial systems require correctness guarantees from day one — retrofitting Money value objects or double-entry accounting is prohibitively expensive.

**Delivers:**
- Shared domain primitives (Entity, ValueObject, AggregateRoot, DomainEvent)
- Money value object (immutable, integer cents storage, currency-safe arithmetic)
- Account aggregate (balance management, withdrawal validation)
- Repository pattern with data mappers
- PostgreSQL schema with proper indexes
- Security infrastructure (field-level encryption, KMS integration)

**Addresses features:**
- Account management (from FEATURES.md: multi-account support)
- Foundation for all financial calculations

**Avoids pitfalls:**
- Floating-point money (Pitfall #1)
- Anemic domain model (Pitfall #2)
- Insecure storage (Pitfall #3)

**Research flag:** Standard patterns — well-documented DDD foundation. Skip `/gsd:research-phase`.

### Phase 2: Transaction Domain (Double-Entry Model)
**Rationale:** Transactions are the core domain. Must implement double-entry from the start — single-entry doesn't scale to transfers, splits, or reconciliation. This is the most complex domain modeling challenge.

**Delivers:**
- Transaction aggregate with double-entry model
- TransactionEntry entity (debit/credit pairs)
- Transfer domain service (cross-account validation)
- Manual transaction creation
- Transaction list with search/filter
- Basic categorization (assign, bulk edit, merchant patterns)
- Split transaction support

**Addresses features:**
- Transaction list (FEATURES.md: table stakes)
- Manual transactions (FEATURES.md: MVP)
- Categorization (FEATURES.md: table stakes)
- Split transactions (FEATURES.md: table stakes)
- Transfer detection (FEATURES.md: table stakes)

**Avoids pitfalls:**
- Improper double-entry (Pitfall #5)
- Treating transfers as two transactions (anti-pattern)

**Research flag:** Needs deeper research — double-entry accounting patterns specific to personal finance, transfer matching algorithms, categorization heuristics.

### Phase 3: Bank Integration (Plaid)
**Rationale:** Enables automatic transaction import. Depends on Phase 2 (Transaction domain) being solid. Integration complexity is high; port/adapter pattern isolates risk.

**Delivers:**
- Plaid Link integration (OAuth flow)
- Plaid access token storage (encrypted)
- Transaction sync via Plaid API (incremental with cursor)
- Webhook handlers (SYNC_UPDATES_AVAILABLE, ITEM_LOGIN_REQUIRED, PENDING_DISCONNECT)
- Reconciliation service (match imported to manual transactions)
- Background job infrastructure (ARQ/BullMQ)
- Connection health dashboard

**Addresses features:**
- Bank account sync (FEATURES.md: table stakes)
- Automatic transaction import (FEATURES.md: table stakes)

**Avoids pitfalls:**
- Plaid error handling (Pitfall #4)
- Synchronous API calls (performance trap)
- Webhook delivery failures (integration gotcha)

**Research flag:** Needs deeper research — Plaid webhook patterns, reconciliation algorithms, duplicate detection strategies, OAuth consent lifecycle.

### Phase 4: Budgeting & Reporting
**Rationale:** Builds on transaction data. Light CQRS enables performant reports without event sourcing complexity. Budgeting is table stakes but not as architecturally complex as transactions.

**Delivers:**
- Budget aggregate (category limits, period definitions)
- Budget status calculations (spent vs. remaining)
- Budget alerts (domain events trigger notifications)
- Spending reports (by category, time period, trends)
- Net worth tracking (assets minus liabilities)
- Data export (CSV)
- Materialized views for dashboard queries

**Addresses features:**
- Basic budgets (FEATURES.md: table stakes)
- Basic reports (FEATURES.md: table stakes)
- Net worth view (FEATURES.md: MVP)
- Data export (FEATURES.md: table stakes)

**Avoids pitfalls:**
- N+1 queries (performance trap)
- Calculating balance from sum (performance trap)

**Research flag:** Standard patterns — budgeting logic is well-understood, CQRS for reports is documented. Skip `/gsd:research-phase`.

### Phase 5: Mobile & Multi-User
**Rationale:** Extends primary interface to mobile. Multi-user support is architectural (affects authentication, authorization, data isolation) so must come before advanced features.

**Delivers:**
- iOS app (React Native or native Swift)
- Android app
- Multi-user authentication (separate logins, JWT claims)
- Shared household view (couples support)
- Account/transaction visibility controls

**Addresses features:**
- Mobile app (FEATURES.md: table stakes)
- Multi-user/couples (FEATURES.md: table stakes)

**Avoids pitfalls:**
- None specific to this phase

**Research flag:** Needs research — React Native vs native, authentication patterns for financial apps, data isolation strategies for multi-tenant.

### Phase 6: Power Features (Reconciliation, Investments, Goals)
**Rationale:** Differentiators that attract Quicken power users. Requires solid foundation from prior phases. Can be split into sub-phases if needed.

**Delivers:**
- Reconciliation workflow (bank statement matching)
- Recurring transaction detection and management
- Investment account balances
- Investment holdings tracking (future sub-phase: cost basis, tax lots)
- Goals with account association
- Bill calendar view
- Cash flow forecasting

**Addresses features:**
- Reconciliation (FEATURES.md: v1.x, differentiator)
- Recurring transactions (FEATURES.md: v1.x)
- Investment tracking (FEATURES.md: v1.x balances, v2+ holdings)
- Goals (FEATURES.md: v1.x)
- Cash flow forecast (FEATURES.md: v1.x)

**Avoids pitfalls:**
- Reconciliation bugs (testing challenge)
- Investment tracking complexity (holdings vs balances)

**Research flag:** Needs research — reconciliation UI/UX patterns, investment data modeling, recurring transaction detection algorithms.

### Phase Ordering Rationale

**Dependency-driven order:**
1. Foundation must come first — cannot build financial features without Money value object and domain primitives
2. Transactions depend on Accounts — cannot record transactions without accounts to debit/credit
3. Plaid integration depends on Transaction domain — imported transactions must fit the domain model
4. Budgeting depends on categorized Transactions — cannot track spending without transaction data
5. Power features depend on all prior phases — reconciliation needs transactions + sync, investments need accounts + transactions

**Risk mitigation order:**
- Critical pitfalls addressed in Phase 1 (money, security, domain modeling)
- Integration complexity isolated in Phase 3 (Plaid)
- Performance optimization deferred until data model is stable (Phase 4+)

**Value delivery order:**
- Phase 1-2: Not user-visible but prevents rewrites
- Phase 3: First major user value (automatic sync)
- Phase 4: MVP feature-complete (budgeting + reports)
- Phase 5: Platform expansion (mobile, multi-user)
- Phase 6: Competitive differentiation (power features)

### Research Flags

**Phases needing `/gsd:research-phase` during planning:**

- **Phase 2 (Transaction Domain):** Double-entry accounting patterns, transfer detection algorithms, categorization heuristics, split transaction UI patterns
- **Phase 3 (Bank Integration):** Plaid webhook handling, reconciliation algorithms, duplicate detection, OAuth lifecycle management, error recovery strategies
- **Phase 5 (Mobile):** React Native vs native Swift/Kotlin, mobile-specific financial app UX patterns, secure token storage on mobile
- **Phase 6 (Power Features):** Reconciliation workflows, recurring transaction detection, investment data modeling, cost basis calculation methods

**Phases with standard patterns (skip research):**

- **Phase 1 (Foundation):** Well-documented DDD patterns, established security practices (encryption, KMS)
- **Phase 4 (Budgeting):** Budgeting logic is straightforward, CQRS patterns well-understood

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core stack validated via official docs; supporting libraries verified on PyPI/npm; version compatibility confirmed |
| Features | MEDIUM-HIGH | Based on competitor analysis (Monarch, YNAB, Copilot, Lunch Money) and Quicken alternative research; user expectations well-documented |
| Architecture | HIGH | DDD + Clean Architecture patterns verified via multiple authoritative sources; hexagonal architecture well-suited for multi-interface; financial domain patterns from production systems |
| Pitfalls | HIGH | Critical pitfalls verified across multiple sources; double-entry, money handling, and Plaid integration patterns from Plaid official docs and production fintech blogs |

**Overall confidence:** HIGH

### Gaps to Address

**Multi-currency handling:** Research indicates complexity but sparse implementation details. Defer to Phase 2+ and research during planning if needed. Base currency budgeting is well-understood; full multi-currency requires exchange rate APIs and unrealized gains tracking.

**Investment tracking (holdings level):** Cost basis calculation methods (FIFO/LIFO/specific lot), stock splits, dividend reinvestment are complex. Defer to Phase 6 sub-phase with dedicated research. Balance-only tracking is straightforward.

**ESPP/stock options:** Very specialized domain; sparse documentation. Likely needs domain expert consultation during Phase 6 if prioritized. Not critical for MVP.

**Mobile authentication:** Biometric auth, secure enclave usage, certificate pinning need mobile-specific security research during Phase 5 planning.

**Reconciliation UX:** Matching algorithm patterns exist, but optimal UX is less documented. May need user testing iteration during Phase 6.

**AI insights:** Deferred to v2+, but if prioritized, needs research on LLM integration patterns, prompt engineering for financial queries, and privacy considerations for sending transaction data to LLM providers.

## Sources

### Primary (HIGH confidence)
- FastAPI Official Docs — Testing, dependencies, async patterns
- SQLAlchemy 2.0 Documentation — ORM patterns, imperative mapping
- Pydantic Settings Docs — Configuration management
- Plaid API Documentation — Official integration guide, webhook handling, error codes
- Plaid Launch Checklist — Production readiness requirements
- TanStack Query Docs — Server state management patterns
- Zustand Documentation — Client state management
- OpenTelemetry FastAPI Instrumentation — Official observability setup
- Martin Fowler: Repository Pattern — Data access patterns
- ByteByteGo: Domain-Driven Design Demystified — DDD fundamentals
- Modern Treasury: Floats Don't Work For Storing Cents — Money handling
- Microsoft: CQRS Pattern — Read/write separation

### Secondary (MEDIUM confidence)
- NerdWallet: Best Budget Apps 2026 — Competitor feature analysis
- Monarch vs YNAB comparison pages — Feature differentiation
- Rob Berger: Best Quicken Alternatives 2026 — Target user needs
- GitHub: fastapi-clean-example — DDD + Clean Architecture patterns
- GitHub: python-clean-architecture — Production template
- Cosmic Python: Repository Pattern — Implementation guidance
- Khalil Stemmler: DTOs, Mappers, Repository in TypeScript DDD — Pattern translation
- Double-Entry Accounting for Engineers (Anvil Works) — Financial domain modeling
- BullMQ Official — Background job patterns
- Medium: Demystifying Double Entry Accounting for Software Engineers — Financial fundamentals
- SSW Rules: Anemic vs Rich Domain Models — DDD anti-patterns

### Tertiary (LOW confidence, needs validation)
- Firefly III Architecture — Open-source personal finance architecture reference
- DDD Tutorial Personal Finance (GitHub) — Community implementation examples
- Actual Budget (open source) — Privacy-focused architecture patterns

---

*Research completed: 2026-01-29*
*Ready for roadmap: yes*
