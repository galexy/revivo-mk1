# Roadmap: Personal Finance Platform

## Overview

A 32-phase journey to build a modern personal finance platform that replaces Quicken with proper domain modeling, data sovereignty, and multi-interface access. The roadmap follows dependency order: domain primitives first, then core entities (accounts, transactions), then authentication, then CI/code quality, then type safety and ORM improvements, then frontend infrastructure, then UI features, then integrations (bank sync), then financial features (budgeting, reporting, investments), migration from legacy systems, and finally platform hardening with multi-user household support. Phases 1-26 deliver the core platform; Phases 27-32 are a future milestone for security hardening and multi-user features. Each phase delivers a coherent, verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Domain primitives, clean architecture scaffolding, devcontainer setup
- [x] **Phase 2: Account Domain** - Account aggregate with all account types and balance tracking
- [x] **Phase 3: Transaction Domain** - Transaction model with categories, splits, and transfers
- [x] **Phase 3.1: Split Identity & Validation Fixes** - Add split IDs, fix validation, category types (INSERTED)
- [x] **Phase 3.2: Add Missing PATCH Test Cases** - Comprehensive PATCH edge case tests (INSERTED)
- [x] **Phase 4: Authentication Infrastructure** - User domain model, JWT issuance, protected routes
- [x] **Phase 4.1: Test Schema Parity** - Align SQLAlchemy metadata with Alembic migrations so tests use production-equivalent schema (INSERTED)
- [x] **Phase 4.2: Current User Metadata Endpoint** - Add /auth/me endpoint returning authenticated user profile (INSERTED)
- [x] **Phase 5: Domain Event Publishing** - Event bus infrastructure, async event handlers, event-driven architecture
- [x] **Phase 6: Transactional Email Infrastructure** - Email domain, SMTP adapter, Mailpit dev env, verification email on registration
- [x] **Phase 7: Nx Monorepo Restructure** - Convert to Nx monorepo with backend and frontend apps
- [x] **Phase 8: CI & Code Quality** - Fix CI pipeline, code coverage, linting, type checking for green CI
- [x] **Phase 9: Type Safety & Test Cleanup** - CategoryTree TypedDict, remove redundant immutability tests
- [ ] **Phase 10: Value Object ORM Mapping** - SQLAlchemy composite() for Money, InstitutionDetails, RewardsBalance
- [ ] **Phase 11: Domain Test Coverage** - Transaction, Category, Payee domain unit tests
- [ ] **Phase 12: Frontend Infrastructure** - React, Tailwind v4, shadcn/ui, Playwright, Claude browsing skill
- [ ] **Phase 13: Login UI** - Login page, session/token management, logout
- [ ] **Phase 14: Frontend API & Routing** - TanStack Query, TanStack Router, state management patterns
- [ ] **Phase 15: API Integration Validation** - Simple account/transaction CRUD to prove infrastructure
- [ ] **Phase 16: Error Handling Patterns** - Transient/system/user errors, UX patterns, CLAUDE.md standards
- [ ] **Phase 17: Transaction UI (Simple)** - Checking/savings transactions, inline editing, auto-create payees/categories
- [ ] **Phase 18: Split Transactions UI** - Create and update split transactions
- [ ] **Phase 19: Transfers UI** - Account transfers, transfers in splits
- [ ] **Phase 20: Pagination & Infinite Scroll** - API pagination, infinite scroll UI
- [ ] **Phase 21: Scheduled Transactions** - Recurring transactions with auto-creation
- [ ] **Phase 22: Bank Sync** - Plaid integration with transaction import and reconciliation
- [ ] **Phase 23: Budgeting** - Envelope budgeting with category tracking
- [ ] **Phase 24: Reporting** - Spending reports, net worth, and trend analysis
- [ ] **Phase 25: Investment Tracking** - Securities, holdings, cost basis, and gains
- [ ] **Phase 26: Migration & Polish** - Quicken import, observability dashboards, comprehensive testing

---

### Future Milestone: Platform Hardening & Multi-User

*These phases address deferred items from Phase 4 (Authentication Infrastructure) and complete the multi-user vision.*

- [ ] **Phase 27: Password Reset** - Email-based password recovery flow
- [ ] **Phase 28: Auth Security Hardening** - Rate limiting, account lockout, brute force protection
- [ ] **Phase 29: Session Management** - View active sessions, logout all devices, token revocation
- [ ] **Phase 30: OIDC & Social Login** - Google OAuth and other identity providers
- [ ] **Phase 31: Multi-User Households** - Invite users to join existing households
- [ ] **Phase 32: User Preferences & Profile** - Timezone, currency, date format, avatar, profile data

## Phase Details

### Phase 1: Foundation
**Goal**: Establish architectural foundation with domain primitives, clean architecture scaffolding, and development environment that enforces correctness guarantees
**Depends on**: Nothing (first phase)
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-06, ARCH-07, ARCH-08, ARCH-09, ARCH-10, ARCH-11, ARCH-12
**Success Criteria** (what must be TRUE):
  1. Developer can open project in devcontainer and run tests with single command
  2. Domain layer code has zero imports from infrastructure or framework packages (verified by lint rule)
  3. Money value object performs arithmetic without precision loss (verified by property tests)
  4. Database schema exists with proper migrations and can be applied to fresh database
  5. Security infrastructure encrypts sensitive fields at rest (verified by inspecting stored data)
**Plans**: 6 plans

Plans:
- [x] 01-01-PLAN.md — Development environment (devcontainer, Docker Compose, tooling)
- [x] 01-02-PLAN.md — Domain primitives (Money, EntityId, ports, events)
- [x] 01-03-PLAN.md — Property-based tests for Money value object
- [x] 01-04-PLAN.md — Persistence infrastructure (SQLAlchemy, migrations, outbox)
- [x] 01-05-PLAN.md — Security and API scaffolding (encryption, FastAPI)
- [x] 01-06-PLAN.md — Integration tests and verification checkpoint

### Phase 2: Account Domain
**Goal**: Users can create and manage all supported account types with proper balance tracking
**Depends on**: Phase 1
**Requirements**: ACCT-01, ACCT-02, ACCT-03, ACCT-04, ACCT-05, ACCT-06, ACCT-07, ACCT-08, ACCT-09, ACCT-10, ACCT-11
**Success Criteria** (what must be TRUE):
  1. User can create checking, savings, credit card, loan, brokerage, IRA, and rewards accounts with starting balances
  2. User can edit account name and properties after creation
  3. User can delete an account (system prevents deletion if transactions exist)
  4. User can view current balance for each account
  5. User can view historical balance for an account over time
**Plans**: 6 plans

Plans:
- [x] 02-01-PLAN.md — Account type enums, value objects, and domain events
- [x] 02-02-PLAN.md — Account aggregate root entity with factory methods
- [x] 02-03-PLAN.md — Persistence layer (table, migration, mapper, repository)
- [x] 02-04-PLAN.md — AccountService application service
- [x] 02-05-PLAN.md — REST API endpoints with Pydantic schemas
- [x] 02-06-PLAN.md — Integration tests and verification checkpoint

### Phase 3: Transaction Domain
**Goal**: Users can record financial transactions with categories, splits, and transfers
**Depends on**: Phase 2
**Requirements**: TRAN-01, TRAN-02, TRAN-03, TRAN-04, TRAN-05, TRAN-06, TRAN-09, TRAN-10, TRAN-11, TRAN-12 (TRAN-07, TRAN-08 deferred - attachments)
**Success Criteria** (what must be TRUE):
  1. User can create, edit, and delete transactions with date, amount, payee, category, and account
  2. User can split a transaction across multiple categories with specific amounts
  3. User can record a transfer between two accounts as a single transaction that affects both balances
  4. User can search and filter transactions by payee, category, amount, date, or account
  5. (Deferred) User can attach receipt files to transactions and view all attachments
**Plans**: 7 plans

Plans:
- [x] 03-01-PLAN.md — Transaction domain primitives (types, enums, SplitLine, Payee, events)
- [x] 03-02-PLAN.md — Transaction aggregate and Category entity with repository protocols
- [x] 03-03-PLAN.md — Database tables and Alembic migration
- [x] 03-04-PLAN.md — ORM mappers and repository implementations
- [x] 03-05-PLAN.md — TransactionService and CategoryService application services
- [x] 03-06-PLAN.md — REST API endpoints for transactions and categories
- [x] 03-07-PLAN.md — Integration tests and verification checkpoint

### Phase 3.1: Split Identity & Validation Fixes (INSERTED)
**Goal**: Fix UAT issues from Phase 3 - add split identity for proper PATCH semantics, improve validation, add category types
**Depends on**: Phase 3
**Requirements**: Fixes for UAT issues 6, 16, 19, 24
**Success Criteria** (what must be TRUE):
  1. SplitLine has unique ID; PATCH can update specific splits by ID
  2. Mirror transactions link to source split via source_split_id
  3. Invalid account/category IDs return 400 (not 500)
  4. Split must have exactly one of category_id or transfer_account_id
  5. Categories have income/expense type
**Plans**: 4 plans

Plans:
- [x] 03.1-01-PLAN.md — SplitId + SplitLine domain (entity identity)
- [x] 03.1-02-PLAN.md — CategoryType (full vertical slice: domain, migration, API, tests)
- [x] 03.1-03-PLAN.md — Split identity persistence/API (migration, repos, schemas, exception handler)
- [x] 03.1-04-PLAN.md — Split identity tests

### Phase 3.2: Add Missing PATCH Test Cases (INSERTED)
**Goal**: Add comprehensive PATCH endpoint tests for edge cases specified in 03.1-CONTEXT.md but not covered during Phase 3.1
**Depends on**: Phase 3.1
**Requirements**: Test coverage for PATCH modification sub-cases (M1-M6)
**Success Criteria** (what must be TRUE):
  1. PATCH tests cover all 6 modification sub-cases (amount change, category change, destination change, conversions)
  2. PATCH tests cover split addition and removal scenarios
  3. PATCH tests verify mirror lifecycle (create/update/delete) during split changes
  4. Invalid split ID in PATCH returns 400
**Plans**: 3 plans

Plans:
- [x] 03.2-01-PLAN.md — PATCH modification sub-cases (M1-M6)
- [x] 03.2-02-PLAN.md — Split addition and removal scenarios
- [x] 03.2-03-PLAN.md — PATCH-specific validation errors

### Phase 4: Authentication Infrastructure
**Goal**: Secure API with user authentication - JWT-based auth with protected routes
**Depends on**: Phase 3.2
**Requirements**: API-01, WEB-02, WEB-03
**Success Criteria** (what must be TRUE):
  1. User domain model exists with persistence (User entity, migration, repository)
  2. User can obtain JWT token via login endpoint
  3. Protected API routes reject requests without valid JWT (401)
  4. Protected API routes accept requests with valid JWT and identify user
  5. Existing E2E tests updated to work with authentication
**Plans**: 8 plans

Plans:
- [x] 04-01-PLAN.md — User and Household domain entities with HouseholdId
- [x] 04-02-PLAN.md — Security infrastructure (PyJWT, pwdlib/Argon2, itsdangerous)
- [x] 04-03-PLAN.md — Database migration for auth tables and household scoping
- [x] 04-04-PLAN.md — ORM mappers and repositories (User, Household, RefreshToken)
- [x] 04-05-PLAN.md — AuthService application service (TDD)
- [x] 04-06-PLAN.md — Auth API routes, schemas, dependencies, and endpoint tests (TDD)
- [x] 04-07-PLAN.md — Route protection and household scoping (TDD)
- [x] 04-08-PLAN.md — Update existing E2E tests for auth and household isolation

### Phase 4.1: Test Schema Parity (INSERTED)
**Goal**: Eliminate schema drift between SQLAlchemy table metadata and Alembic migrations so integration tests run against a production-equivalent schema
**Depends on**: Phase 4
**Requirements**: TEST integrity
**Success Criteria** (what must be TRUE):
  1. Integration tests create tables using Alembic migrations (not metadata.create_all)
  2. All FK constraints, indexes, and column properties in migrations are reflected in SQLAlchemy metadata (or vice versa)
  3. No test can pass against a schema that differs from production
  4. All existing tests still pass
**Plans**: 2 plans

Plans:
- [x] 04.1-01-PLAN.md — Fix Alembic config and replace hand-written migrations with autogenerated
- [x] 04.1-02-PLAN.md — Drift detection test and autogenerate-first knowledge encoding

### Phase 4.2: Current User Metadata Endpoint (INSERTED)
**Goal**: Add a /auth/me endpoint that returns the authenticated user's profile metadata (user_id, email, display_name, household_id, email_verified status)
**Depends on**: Phase 4
**Requirements**: WEB-02 (user identity)
**Success Criteria** (what must be TRUE):
  1. GET /auth/me with valid JWT returns user profile (user_id, email, display_name, household_id, email_verified)
  2. GET /auth/me without JWT returns 401
  3. Response does not leak sensitive fields (password_hash, internal IDs)
**Plans**: 1 plan

Plans:
- [x] 04.2-01-PLAN.md — Add /auth/me endpoint with UserProfileResponse schema and integration tests

### Phase 5: Domain Event Publishing
**Goal**: Establish domain event publishing infrastructure that enables async event handlers and event-driven architecture patterns
**Depends on**: Phase 4.2
**Requirements**: ARCH event-driven patterns
**Success Criteria** (what must be TRUE):
  1. Event bus infrastructure exists for publishing domain events
  2. Event handlers can subscribe to specific event types
  3. Events can be published synchronously (in-process) or queued for async handling
  4. Event publishing integrates with existing domain events (UserRegistered, etc.)
  5. Test infrastructure supports event handler testing
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — Event bus infrastructure and dependencies (Procrastinate, jobs database)
- [x] 05-02-PLAN.md — Job queue wiring, UoW event publishing, handler registration
- [x] 05-03-PLAN.md — Operational scripts and runbook for job queue management

### Phase 6: Transactional Email Infrastructure
**Goal**: Build email sending domain with SMTP adapter, add Mailpit to dev environment for email testing, send verification email on registration
**Depends on**: Phase 5
**Requirements**: AUTH email delivery
**Success Criteria** (what must be TRUE):
  1. Email domain exists with port (EmailService protocol) and SMTP adapter implementation
  2. Mailpit runs in Docker Compose dev environment and captures all outgoing emails
  3. UserRegistered event handler triggers verification email containing the signed token link
  4. Integration tests mock the email adapter (no real SMTP calls) and verify email send was invoked with correct arguments
  5. Password reset and other future transactional emails can reuse the same infrastructure
  6. Dev workflow: register user -> open Mailpit UI -> click verification link -> user verified
**Plans**: 5 plans

Plans:
- [x] 06-01-PLAN.md — EmailService protocol and SMTP adapter with Jinja2 templates
- [x] 06-02-PLAN.md — Mailpit Docker Compose and SMTP configuration
- [x] 06-03-PLAN.md — Event handler and job queue email integration
- [x] 06-04-PLAN.md — Integration tests and end-to-end verification
- [x] 06-05-PLAN.md — Async event bus, UoW, services, and routes conversion

### Phase 7: Nx Monorepo Restructure
**Goal**: Convert project to Nx monorepo structure to support multiple apps and shared libraries
**Depends on**: Phase 6
**Requirements**: Monorepo structure (apps/api, apps/web scaffold, libs/domain, libs/ui scaffold)
**Success Criteria** (what must be TRUE):
  1. Project uses Nx monorepo structure
  2. Backend exists as app at `apps/backend/` (or `apps/api/`)
  3. Frontend scaffold exists as app at `apps/frontend/` (or `apps/web/`)
  4. Libraries directory structure ready at `libs/`
  5. All existing backend tests pass after restructure
  6. Nx commands work for building and testing apps
**Plans**: 4 plans

Plans:
- [x] 07-01-PLAN.md — Initialize Nx workspace, scaffold apps/web/ and libs/ui/
- [x] 07-02-PLAN.md — Move backend to apps/api/ with config updates
- [x] 07-03-PLAN.md — Extract domain layer to libs/domain/, rewrite imports
- [x] 07-04-PLAN.md — Update CLAUDE.md, final verification and smoke test

### Phase 8: CI & Code Quality
**Goal**: Get CI pipeline green and establish code quality baseline -- fix linting errors, resolve pyright strict type errors, add code coverage to Nx targets
**Depends on**: Phase 7
**Requirements**: CI pipeline health, code quality
**Success Criteria** (what must be TRUE):
  1. GitHub Actions CI passes on all jobs (lint, typecheck, test)
  2. All pyright strict errors resolved in api and domain projects
  3. All ruff lint errors resolved in api and domain projects
  4. Code coverage Nx targets configured and reporting
  5. import-linter passes in CI
**Plans**: 5 plans

Plans:
- [x] 08-01-PLAN.md — Tooling config (pyrightconfig.json, py.typed, ruff config, format) + domain fixes
- [x] 08-02-PLAN.md — API pyright strict error fixes (repositories, mappers, routes, tests)
- [x] 08-03-PLAN.md — API ruff lint error fixes (DTZ, imports, unused args, exception chaining)
- [x] 08-04-PLAN.md — Coverage Nx targets + CI restructure (nx affected, caching, blocking checks)
- [x] 08-05-PLAN.md — Nx format targets, CI nx affected for format, pyright warning fix

### Phase 9: Type Safety & Test Cleanup
**Goal**: Improve type safety by replacing loosely-typed returns with TypedDicts, and remove tests made redundant by pyright strict mode
**Depends on**: Phase 8
**Requirements**: Code quality
**Success Criteria** (what must be TRUE):
  1. get_category_tree returns a CategoryTree TypedDict with distinct types per key
  2. categories.py has zero type: ignore comments for tree access
  3. No redundant immutability tests exist for frozen dataclasses (pyright strict catches these at compile time)
**Plans**: 1 plan

Plans:
- [x] 09-01-PLAN.md — CategoryTree TypedDict + remove redundant immutability tests

### Phase 10: Value Object ORM Mapping
**Goal**: Replace manual value object decomposition/reconstruction with SQLAlchemy composite() mappings
**Depends on**: Phase 8
**Requirements**: Code quality, ORM correctness
**Success Criteria** (what must be TRUE):
  1. SQLAlchemy composite() maps Money, InstitutionDetails, RewardsBalance to flat DB columns
  2. _decompose_value_objects before_flush handler is removed
  3. Manual value object reconstruction in AccountRepository is removed
  4. 20+ type: ignore[attr-defined] comments eliminated from mappers.py
  5. All existing tests pass
**Plans**: 1 plan

Plans:
- [ ] 10-01-PLAN.md — SQLAlchemy composite() for Money, InstitutionDetails, RewardsBalance

### Phase 11: Domain Test Coverage
**Goal**: Add domain unit tests for models that currently have zero domain-level coverage
**Depends on**: Phase 8
**Requirements**: TEST-01 (domain layer comprehensive unit tests)
**Success Criteria** (what must be TRUE):
  1. Transaction domain model has unit tests covering create, update, status changes, splits, and events
  2. Category domain model has unit tests covering create, update, delete, hierarchy, system categories
  3. Payee domain model has unit tests covering create, update, usage tracking
  4. Domain coverage increases from 48% toward 70%+
**Plans**: 1 plan

Plans:
- [ ] 11-01-PLAN.md — Transaction, Category, Payee domain unit tests

### Phase 12: Frontend Infrastructure
**Goal**: Set up frontend tooling and testing infrastructure
**Depends on**: Phase 8
**Requirements**: ARCH-06, TEST-05
**Success Criteria** (what must be TRUE):
  1. React app runs with Tailwind CSS v4
  2. shadcn/ui component library integrated and working
  3. Playwright configured for E2E UI testing
  4. Claude browsing skill available for launching site and testing UI changes
  5. Basic smoke test passes (app renders without errors)
**Plans**: TBD

Plans:
- [ ] 12-01: TBD
- [ ] 12-02: TBD

### Phase 13: Login UI
**Goal**: User can log in and out via web interface
**Depends on**: Phase 12
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04
**Success Criteria** (what must be TRUE):
  1. Login page with form (email/password or OAuth)
  2. Successful login stores JWT token and redirects to app
  3. Session persists across browser refresh
  4. User can log out from any page
  5. Unauthenticated users redirected to login
**Plans**: TBD

Plans:
- [ ] 13-01: TBD
- [ ] 13-02: TBD

### Phase 14: Frontend API & Routing
**Goal**: Establish patterns for API communication and client-side routing
**Depends on**: Phase 13
**Requirements**: WEB-08, ARCH-07
**Success Criteria** (what must be TRUE):
  1. TanStack Query configured for API state management
  2. TanStack Router configured for client-side routing
  3. Type-safe API client generated from OpenAPI spec
  4. Authentication token automatically included in API requests
  5. API error responses handled consistently
**Plans**: TBD

Plans:
- [ ] 14-01: TBD
- [ ] 14-02: TBD

### Phase 15: API Integration Validation
**Goal**: Validate frontend-backend integration with minimal CRUD operations
**Depends on**: Phase 14
**Requirements**: WEB-06, WEB-07
**Success Criteria** (what must be TRUE):
  1. User can create an account via UI
  2. User can update an account via UI
  3. User can create a transaction with single split via UI
  4. User can update a transaction via UI
  5. E2E tests cover these flows
  6. Claude browsing skill used to automate UAT
**Plans**: TBD

Plans:
- [ ] 15-01: TBD
- [ ] 15-02: TBD

### Phase 16: Error Handling Patterns
**Goal**: Define and implement consistent error handling across the UI
**Depends on**: Phase 15
**Requirements**: WEB-06, WEB-07
**Success Criteria** (what must be TRUE):
  1. Transient errors (network) show retry UI
  2. System errors show appropriate error message
  3. User errors (validation) show inline feedback
  4. Error handling patterns documented in frontend CLAUDE.md
  5. Reusable error UI components created
**Plans**: TBD

Plans:
- [ ] 16-01: TBD
- [ ] 16-02: TBD

### Phase 17: Transaction UI (Simple Accounts)
**Goal**: Full transaction management for checking/savings accounts
**Depends on**: Phase 16
**Requirements**: TRAN-01, TRAN-02, TRAN-03, TRAN-04, TRAN-11
**Success Criteria** (what must be TRUE):
  1. Transaction list view for checking/savings accounts
  2. Inline editing of transaction fields
  3. Auto-create payees when typing new payee name
  4. Auto-create categories when typing new category name
  5. Delete transaction with confirmation
  6. No split transaction editing (single category only)
**Plans**: TBD

Plans:
- [ ] 17-01: TBD
- [ ] 17-02: TBD
- [ ] 17-03: TBD

### Phase 18: Split Transactions UI
**Goal**: Support creating and editing split transactions
**Depends on**: Phase 17
**Requirements**: TRAN-05
**Success Criteria** (what must be TRUE):
  1. User can split transaction across multiple categories
  2. Split amounts must sum to transaction total
  3. User can add/remove split lines
  4. User can edit individual split amounts and categories
**Plans**: TBD

Plans:
- [ ] 18-01: TBD
- [ ] 18-02: TBD

### Phase 19: Transfers UI
**Goal**: Support transfers between accounts in the UI
**Depends on**: Phase 18
**Requirements**: TRAN-06
**Success Criteria** (what must be TRUE):
  1. User can create transfer between two accounts
  2. Transfer shows in both account transaction lists
  3. User can create split with transfer component
  4. Editing transfer updates both sides
**Plans**: TBD

Plans:
- [ ] 19-01: TBD
- [ ] 19-02: TBD

### Phase 20: Pagination & Infinite Scroll
**Goal**: Handle large transaction lists efficiently
**Depends on**: Phase 19
**Requirements**: API-05, API-06
**Success Criteria** (what must be TRUE):
  1. Transaction API supports cursor-based pagination
  2. UI implements infinite scroll for transaction list
  3. Scroll position preserved on navigation
  4. Performance acceptable with 10,000+ transactions
**Plans**: TBD

Plans:
- [ ] 20-01: TBD
- [ ] 20-02: TBD

### Phase 21: Scheduled Transactions
**Goal**: Users can define recurring transactions that automatically create instances on schedule
**Depends on**: Phase 20
**Requirements**: SCHED-01, SCHED-02, SCHED-03, SCHED-04, SCHED-05, SCHED-06, SCHED-07
**Success Criteria** (what must be TRUE):
  1. User can create recurring transaction with frequency (weekly, monthly, yearly, custom) and date range
  2. System automatically creates transaction instances when due date arrives
  3. User can manually record next instance before due date
  4. User can edit future instances without affecting past ones
  5. User can skip or delete scheduled transaction series
**Plans**: TBD

Plans:
- [ ] 21-01: TBD
- [ ] 21-02: TBD

### Phase 22: Bank Sync
**Goal**: Users can connect bank accounts via Plaid and have transactions automatically imported and reconciled
**Depends on**: Phase 21
**Requirements**: PLAID-01, PLAID-02, PLAID-03, PLAID-04, PLAID-05, PLAID-06, PLAID-07, PLAID-08, PLAID-09, RECON-01, RECON-02, RECON-03, RECON-04, RECON-05
**Success Criteria** (what must be TRUE):
  1. User can connect checking and credit card accounts via Plaid OAuth flow
  2. System syncs transactions from connected accounts and creates new transactions automatically
  3. System matches downloaded transactions to existing manual entries and user can confirm or reject matches
  4. System auto-categorizes new transactions based on historical patterns
  5. User can view connection health status and disconnect accounts
**Plans**: TBD

Plans:
- [ ] 22-01: TBD
- [ ] 22-02: TBD
- [ ] 22-03: TBD

### Phase 23: Budgeting
**Goal**: Users can create envelope budgets and track spending against category limits
**Depends on**: Phase 22
**Requirements**: BUDG-01, BUDG-02, BUDG-03, BUDG-04, BUDG-05, BUDG-06, BUDG-07, BUDG-08
**Success Criteria** (what must be TRUE):
  1. User can create annual budget with monthly breakdown by category
  2. User can allocate funds to category envelopes and move funds between categories
  3. System tracks actual spending vs budget for each category in real-time
  4. User can see remaining budget amount for each category in current month
  5. User can view budget performance over time with rollover support
**Plans**: TBD

Plans:
- [ ] 23-01: TBD
- [ ] 23-02: TBD

### Phase 24: Reporting
**Goal**: Users can view spending analysis, net worth, and trends across their financial data
**Depends on**: Phase 23
**Requirements**: RPT-01, RPT-02, RPT-03, RPT-04, RPT-05, RPT-06
**Success Criteria** (what must be TRUE):
  1. User can view spending by category for any time period (month, quarter, year)
  2. User can view spending trends over time with visual charts
  3. User can view net worth (assets minus liabilities) as of any date
  4. User can view net worth trend over time
  5. User can filter all reports by date range, account, or category
**Plans**: TBD

Plans:
- [ ] 24-01: TBD
- [ ] 24-02: TBD

### Phase 25: Investment Tracking
**Goal**: Users can track investment holdings with cost basis and gain/loss calculations
**Depends on**: Phase 24
**Requirements**: INV-01, INV-02, INV-03, INV-04, INV-05, INV-06, INV-07, INV-08
**Success Criteria** (what must be TRUE):
  1. User can record buy, sell, dividend, and stock split transactions for securities
  2. System tracks cost basis for each holding using FIFO method
  3. User can view current holdings with shares, cost basis, and current value
  4. System calculates unrealized gain/loss for current holdings
  5. System tracks realized gains/losses on sales
**Plans**: TBD

Plans:
- [ ] 25-01: TBD
- [ ] 25-02: TBD

### Phase 26: Migration & Polish
**Goal**: Users can migrate from Quicken and system has production-ready observability and test coverage
**Depends on**: Phase 25
**Requirements**: MIG-01, MIG-02, MIG-03, MIG-04, MIG-05, MIG-06, MIG-07, OBS-01, OBS-02, OBS-03, OBS-04, OBS-05, OBS-06, OBS-07, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):
  1. User can import complete Quicken transaction history including transfers, attachments, and brokerage transactions
  2. User can map Quicken categories to new structure during import
  3. Grafana dashboards show API metrics, Plaid sync rates, and background job health
  4. All financial mutations are logged with before/after values for audit trail
  5. Test suite covers domain logic, API endpoints, and critical UI workflows with Playwright
**Plans**: TBD

Plans:
- [ ] 26-01: TBD
- [ ] 26-02: TBD
- [ ] 26-03: TBD

---

## Future Milestone: Platform Hardening & Multi-User

*Phases 27-32 address deferred items from Phase 4 and complete the multi-user household vision. These phases can be executed after the core platform is functional.*

### Phase 27: Password Reset
**Goal**: Users can recover account access via email-based password reset
**Depends on**: Phase 26 (or can be pulled earlier if email infrastructure exists from Phase 6)
**Requirements**: AUTH-RESET-01, AUTH-RESET-02
**Success Criteria** (what must be TRUE):
  1. User can request password reset via email
  2. Reset link expires after 24 hours
  3. User can set new password via reset link
  4. Old sessions invalidated after password change
  5. Rate limiting on reset requests prevents abuse
**Plans**: TBD

Plans:
- [ ] 27-01: TBD
- [ ] 27-02: TBD

### Phase 28: Auth Security Hardening
**Goal**: Protect authentication endpoints from brute force and credential stuffing attacks
**Depends on**: Phase 27
**Requirements**: SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):
  1. Login endpoint rate limited per IP and per email
  2. Account locks temporarily after N failed attempts
  3. Lockout duration increases with repeated failures
  4. Admin can unlock accounts manually
  5. Failed login attempts logged for security monitoring
**Plans**: TBD

Plans:
- [ ] 28-01: TBD
- [ ] 28-02: TBD

### Phase 29: Session Management
**Goal**: Users can view and control their active sessions across devices
**Depends on**: Phase 28
**Requirements**: AUTH-SESSION-01, AUTH-SESSION-02, AUTH-SESSION-03
**Success Criteria** (what must be TRUE):
  1. User can view list of active sessions (device, location, last active)
  2. User can logout individual sessions
  3. User can logout all other sessions ("logout everywhere")
  4. Session terminated immediately on logout (refresh token revoked)
  5. Sessions auto-expire after inactivity period
**Plans**: TBD

Plans:
- [ ] 29-01: TBD
- [ ] 29-02: TBD

### Phase 30: OIDC & Social Login
**Goal**: Users can authenticate via external identity providers (Google, etc.)
**Depends on**: Phase 29
**Requirements**: AUTH-OIDC-01, AUTH-OIDC-02, AUTH-OIDC-03
**Success Criteria** (what must be TRUE):
  1. User can sign up and log in via Google OAuth
  2. OAuth accounts linked to existing email accounts automatically
  3. User can link/unlink OAuth providers from settings
  4. Users with only OAuth can add password later
  5. OAuth tokens stored securely and refreshed as needed
**Plans**: TBD

Plans:
- [ ] 30-01: TBD
- [ ] 30-02: TBD

### Phase 31: Multi-User Households
**Goal**: Multiple users can share access to a household's financial data
**Depends on**: Phase 30
**Requirements**: HOUSEHOLD-01, HOUSEHOLD-02, HOUSEHOLD-03
**Success Criteria** (what must be TRUE):
  1. User can invite others to join their household via email
  2. Invited user receives email with join link
  3. Invited user can accept/decline invitation
  4. All household members see same accounts and transactions
  5. Household owner can remove members
**Plans**: TBD

Plans:
- [ ] 31-01: TBD
- [ ] 31-02: TBD

### Phase 32: User Preferences & Profile
**Goal**: Users can customize their experience and manage profile information
**Depends on**: Phase 31
**Requirements**: USER-PREF-01, USER-PREF-02, USER-PROFILE-01
**Success Criteria** (what must be TRUE):
  1. User can set timezone (affects date display)
  2. User can set preferred currency (affects amount display)
  3. User can set date format preference
  4. User can upload profile avatar
  5. User can update display name and contact info
**Plans**: TBD

Plans:
- [ ] 32-01: TBD
- [ ] 32-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 3.1 -> 3.2 -> 4 -> 4.1 -> 4.2 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> ... -> 26 -> 27 -> ... -> 32

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 6/6 | Complete | 2026-01-30 |
| 2. Account Domain | 6/6 | Complete | 2026-01-30 |
| 3. Transaction Domain | 7/7 | Complete | 2026-02-02 |
| 3.1 Split Identity & Validation | 4/4 | Complete | 2026-02-02 |
| 3.2 Add Missing PATCH Tests | 3/3 | Complete | 2026-02-03 |
| 4. Authentication Infrastructure | 8/8 | Complete | 2026-02-05 |
| 4.1 Test Schema Parity | 2/2 | Complete | 2026-02-06 |
| 4.2 Current User Metadata Endpoint | 1/1 | Complete | 2026-02-06 |
| 5. Domain Event Publishing | 3/3 | Complete | 2026-02-06 |
| 6. Transactional Email Infrastructure | 5/5 | Complete | 2026-02-07 |
| 7. Nx Monorepo Restructure | 4/4 | Complete | 2026-02-07 |
| 8. CI & Code Quality | 5/5 | Complete | 2026-02-09 |
| 9. Type Safety & Test Cleanup | 1/1 | Complete | 2026-02-09 |
| 10. Value Object ORM Mapping | 0/1 | Not started | - |
| 11. Domain Test Coverage | 0/1 | Not started | - |
| 12. Frontend Infrastructure | 0/2 | Not started | - |
| 13. Login UI | 0/2 | Not started | - |
| 14. Frontend API & Routing | 0/2 | Not started | - |
| 15. API Integration Validation | 0/2 | Not started | - |
| 16. Error Handling Patterns | 0/2 | Not started | - |
| 17. Transaction UI (Simple) | 0/3 | Not started | - |
| 18. Split Transactions UI | 0/2 | Not started | - |
| 19. Transfers UI | 0/2 | Not started | - |
| 20. Pagination & Infinite Scroll | 0/2 | Not started | - |
| 21. Scheduled Transactions | 0/2 | Not started | - |
| 22. Bank Sync | 0/3 | Not started | - |
| 23. Budgeting | 0/2 | Not started | - |
| 24. Reporting | 0/2 | Not started | - |
| 25. Investment Tracking | 0/2 | Not started | - |
| 26. Migration & Polish | 0/3 | Not started | - |
| **Future Milestone** | | | |
| 27. Password Reset | 0/2 | Not started | - |
| 28. Auth Security Hardening | 0/2 | Not started | - |
| 29. Session Management | 0/2 | Not started | - |
| 30. OIDC & Social Login | 0/2 | Not started | - |
| 31. Multi-User Households | 0/2 | Not started | - |
| 32. User Preferences & Profile | 0/2 | Not started | - |
