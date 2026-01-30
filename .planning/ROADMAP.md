# Roadmap: Personal Finance Platform

## Overview

A 10-phase journey to build a modern personal finance platform that replaces Quicken with proper domain modeling, data sovereignty, and multi-interface access. The roadmap follows dependency order: domain primitives first, then core entities (accounts, transactions), then interfaces, then integrations (bank sync), then financial features (budgeting, reporting, investments), and finally migration from legacy systems. Each phase delivers a coherent, verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Domain primitives, clean architecture scaffolding, devcontainer setup
- [ ] **Phase 2: Account Domain** - Account aggregate with all account types and balance tracking
- [ ] **Phase 3: Transaction Domain** - Double-entry transaction model with categories, splits, and transfers
- [ ] **Phase 4: Web Interface & API** - FastAPI REST endpoints and React frontend shell
- [ ] **Phase 5: Scheduled Transactions** - Recurring transactions with auto-creation
- [ ] **Phase 6: Bank Sync** - Plaid integration with transaction import and reconciliation
- [ ] **Phase 7: Budgeting** - Envelope budgeting with category tracking
- [ ] **Phase 8: Reporting** - Spending reports, net worth, and trend analysis
- [ ] **Phase 9: Investment Tracking** - Securities, holdings, cost basis, and gains
- [ ] **Phase 10: Migration & Polish** - Quicken import, observability dashboards, comprehensive testing

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
- [ ] 02-01-PLAN.md — Account type enums, value objects, and domain events
- [ ] 02-02-PLAN.md — Account aggregate root entity with factory methods
- [ ] 02-03-PLAN.md — Persistence layer (table, migration, mapper, repository)
- [ ] 02-04-PLAN.md — AccountService application service
- [ ] 02-05-PLAN.md — REST API endpoints with Pydantic schemas
- [ ] 02-06-PLAN.md — Integration tests and verification checkpoint

### Phase 3: Transaction Domain
**Goal**: Users can record financial transactions with double-entry accounting, categories, splits, and transfers
**Depends on**: Phase 2
**Requirements**: TRAN-01, TRAN-02, TRAN-03, TRAN-04, TRAN-05, TRAN-06, TRAN-07, TRAN-08, TRAN-09, TRAN-10, TRAN-11, TRAN-12, TRAN-13, TRAN-14
**Success Criteria** (what must be TRUE):
  1. User can create, edit, and delete transactions with date, amount, payee, category, and account
  2. User can split a transaction across multiple categories with specific amounts
  3. User can record a transfer between two accounts as a single transaction that affects both balances
  4. User can attach receipt files to transactions and view all attachments
  5. User can search and filter transactions by payee, category, amount, date, or account
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Web Interface & API
**Goal**: Users can access the application through web browser and external tools can access via REST API
**Depends on**: Phase 3
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04, WEB-05, WEB-06, WEB-07, WEB-08, API-01, API-02, API-03, API-04, API-05, API-06, API-07
**Success Criteria** (what must be TRUE):
  1. User can log in with email/password and session persists across browser refresh
  2. User can log out from any page
  3. UI displays loading states during API calls and error messages for failures
  4. API documentation is available at /docs with all endpoints documented
  5. External tool can authenticate and call API endpoints to list accounts and transactions
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD

### Phase 5: Scheduled Transactions
**Goal**: Users can define recurring transactions that automatically create instances on schedule
**Depends on**: Phase 4
**Requirements**: SCHED-01, SCHED-02, SCHED-03, SCHED-04, SCHED-05, SCHED-06, SCHED-07
**Success Criteria** (what must be TRUE):
  1. User can create recurring transaction with frequency (weekly, monthly, yearly, custom) and date range
  2. System automatically creates transaction instances when due date arrives
  3. User can manually record next instance before due date
  4. User can edit future instances without affecting past ones
  5. User can skip or delete scheduled transaction series
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: Bank Sync
**Goal**: Users can connect bank accounts via Plaid and have transactions automatically imported and reconciled
**Depends on**: Phase 5
**Requirements**: PLAID-01, PLAID-02, PLAID-03, PLAID-04, PLAID-05, PLAID-06, PLAID-07, PLAID-08, PLAID-09, RECON-01, RECON-02, RECON-03, RECON-04, RECON-05
**Success Criteria** (what must be TRUE):
  1. User can connect checking and credit card accounts via Plaid OAuth flow
  2. System syncs transactions from connected accounts and creates new transactions automatically
  3. System matches downloaded transactions to existing manual entries and user can confirm or reject matches
  4. System auto-categorizes new transactions based on historical patterns
  5. User can view connection health status and disconnect accounts
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD
- [ ] 06-03: TBD

### Phase 7: Budgeting
**Goal**: Users can create envelope budgets and track spending against category limits
**Depends on**: Phase 6
**Requirements**: BUDG-01, BUDG-02, BUDG-03, BUDG-04, BUDG-05, BUDG-06, BUDG-07, BUDG-08
**Success Criteria** (what must be TRUE):
  1. User can create annual budget with monthly breakdown by category
  2. User can allocate funds to category envelopes and move funds between categories
  3. System tracks actual spending vs budget for each category in real-time
  4. User can see remaining budget amount for each category in current month
  5. User can view budget performance over time with rollover support
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

### Phase 8: Reporting
**Goal**: Users can view spending analysis, net worth, and trends across their financial data
**Depends on**: Phase 7
**Requirements**: RPT-01, RPT-02, RPT-03, RPT-04, RPT-05, RPT-06
**Success Criteria** (what must be TRUE):
  1. User can view spending by category for any time period (month, quarter, year)
  2. User can view spending trends over time with visual charts
  3. User can view net worth (assets minus liabilities) as of any date
  4. User can view net worth trend over time
  5. User can filter all reports by date range, account, or category
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

### Phase 9: Investment Tracking
**Goal**: Users can track investment holdings with cost basis and gain/loss calculations
**Depends on**: Phase 8
**Requirements**: INV-01, INV-02, INV-03, INV-04, INV-05, INV-06, INV-07, INV-08
**Success Criteria** (what must be TRUE):
  1. User can record buy, sell, dividend, and stock split transactions for securities
  2. System tracks cost basis for each holding using FIFO method
  3. User can view current holdings with shares, cost basis, and current value
  4. System calculates unrealized gain/loss for current holdings
  5. System tracks realized gains/losses on sales
**Plans**: TBD

Plans:
- [ ] 09-01: TBD
- [ ] 09-02: TBD

### Phase 10: Migration & Polish
**Goal**: Users can migrate from Quicken and system has production-ready observability and test coverage
**Depends on**: Phase 9
**Requirements**: MIG-01, MIG-02, MIG-03, MIG-04, MIG-05, MIG-06, MIG-07, OBS-01, OBS-02, OBS-03, OBS-04, OBS-05, OBS-06, OBS-07, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):
  1. User can import complete Quicken transaction history including transfers, attachments, and brokerage transactions
  2. User can map Quicken categories to new structure during import
  3. Grafana dashboards show API metrics, Plaid sync rates, and background job health
  4. All financial mutations are logged with before/after values for audit trail
  5. Test suite covers domain logic, API endpoints, and critical UI workflows with Playwright
**Plans**: TBD

Plans:
- [ ] 10-01: TBD
- [ ] 10-02: TBD
- [ ] 10-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 6/6 | Complete | 2026-01-30 |
| 2. Account Domain | 0/6 | Planned | - |
| 3. Transaction Domain | 0/3 | Not started | - |
| 4. Web Interface & API | 0/3 | Not started | - |
| 5. Scheduled Transactions | 0/2 | Not started | - |
| 6. Bank Sync | 0/3 | Not started | - |
| 7. Budgeting | 0/2 | Not started | - |
| 8. Reporting | 0/2 | Not started | - |
| 9. Investment Tracking | 0/2 | Not started | - |
| 10. Migration & Polish | 0/3 | Not started | - |
