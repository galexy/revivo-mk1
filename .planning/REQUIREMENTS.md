# Requirements: Personal Finance Platform

**Defined:** 2026-01-29
**Core Value:** Own your financial data and access it anywhere through any interface - web, API, CLI, or AI. Your data, your tools, no vendor lock-in.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Account Management

- [ ] **ACCT-01**: User can create checking account with name and starting balance
- [ ] **ACCT-02**: User can create savings account with name and starting balance
- [ ] **ACCT-03**: User can create credit card account with name and starting balance (typically negative)
- [ ] **ACCT-04**: User can create loan/mortgage account with name and starting balance
- [ ] **ACCT-05**: User can create brokerage (equity) account with name and starting balance
- [ ] **ACCT-06**: User can create IRA/retirement account with name and starting balance
- [ ] **ACCT-07**: User can create rewards/miles account with name and starting balance
- [ ] **ACCT-08**: User can edit account name and properties
- [ ] **ACCT-09**: User can delete account (with safeguards if transactions exist)
- [ ] **ACCT-10**: User can view current balance for each account
- [ ] **ACCT-11**: User can view account balance history over time

### Transaction Management

- [ ] **TRAN-01**: User can manually record a transaction with date, amount, payee, category, and account
- [ ] **TRAN-02**: User can edit existing transaction
- [ ] **TRAN-03**: User can delete transaction
- [ ] **TRAN-04**: User can assign transaction to a category
- [ ] **TRAN-05**: User can split transaction across multiple categories with specified amounts
- [ ] **TRAN-06**: User can record transfer between two accounts (single transaction, affects both accounts)
- [ ] **TRAN-07**: User can attach receipt/document file to transaction
- [ ] **TRAN-08**: User can view all attachments on a transaction
- [ ] **TRAN-09**: User can search transactions by payee, category, amount range, or date range
- [ ] **TRAN-10**: User can filter transaction list by account, category, or date range
- [ ] **TRAN-11**: User can view transaction history for an account in chronological order
- [ ] **TRAN-12**: System stores transaction amounts using Decimal precision (no floating point)
- [ ] **TRAN-13**: System implements double-entry accounting (every transaction has balanced debits and credits)
- [ ] **TRAN-14**: System prevents negative balances on accounts that don't allow them (e.g., checking accounts below zero without overdraft)

### Plaid Integration

- [ ] **PLAID-01**: User can connect checking account via Plaid OAuth flow
- [ ] **PLAID-02**: User can connect credit card account via Plaid OAuth flow
- [ ] **PLAID-03**: System stores Plaid access tokens with field-level AES-256 encryption
- [ ] **PLAID-04**: System syncs transactions from connected accounts incrementally
- [ ] **PLAID-05**: System handles Plaid webhook for SYNC_UPDATES_AVAILABLE
- [ ] **PLAID-06**: System handles Plaid webhook for ITEM_LOGIN_REQUIRED
- [ ] **PLAID-07**: System renames payee names intelligently (clean up bank's raw merchant names)
- [ ] **PLAID-08**: User can view connection health status for each Plaid-linked account
- [ ] **PLAID-09**: User can disconnect Plaid account and stop syncing

### Reconciliation

- [ ] **RECON-01**: System matches downloaded transaction to existing manual transaction by amount, date, and payee similarity
- [ ] **RECON-02**: User can confirm suggested match between downloaded and manual transaction
- [ ] **RECON-03**: User can reject suggested match and keep transactions separate
- [ ] **RECON-04**: System creates new transaction from downloaded data if no match found
- [ ] **RECON-05**: System auto-categorizes new transactions based on historical patterns (same payee → same category)

### Scheduled Transactions

- [ ] **SCHED-01**: User can create recurring transaction with frequency (weekly, monthly, yearly, custom)
- [ ] **SCHED-02**: User can specify start date and optional end date for recurring transaction
- [ ] **SCHED-03**: System auto-creates next scheduled transaction instance on due date
- [ ] **SCHED-04**: User can manually record next scheduled instance before due date
- [ ] **SCHED-05**: User can edit future scheduled instances without affecting past
- [ ] **SCHED-06**: User can delete scheduled transaction series
- [ ] **SCHED-07**: User can skip specific instance of scheduled transaction

### Budgeting

- [ ] **BUDG-01**: User can create annual budget with monthly breakdown by category
- [ ] **BUDG-02**: User can set spending limit for each category per month
- [ ] **BUDG-03**: User can allocate funds to category envelopes
- [ ] **BUDG-04**: User can move funds between category envelopes
- [ ] **BUDG-05**: System tracks actual spending vs budget for each category
- [ ] **BUDG-06**: System shows remaining budget amount for each category in current month
- [ ] **BUDG-07**: User can view budget performance by category over time (spent vs limit)
- [ ] **BUDG-08**: System allows rollover of unused budget to next month within same category

### Investment Tracking

- [ ] **INV-01**: User can record buy transaction for security (stock, ETF, mutual fund) with shares and price
- [ ] **INV-02**: User can record sell transaction for security with shares and price
- [ ] **INV-03**: User can record dividend transaction
- [ ] **INV-04**: User can record stock split with ratio
- [ ] **INV-05**: System tracks cost basis for each holding using FIFO method
- [ ] **INV-06**: System calculates unrealized gain/loss for current holdings
- [ ] **INV-07**: User can view list of current holdings with shares, cost basis, current value
- [ ] **INV-08**: System tracks realized gains/losses on sales

### Reporting

- [ ] **RPT-01**: User can view spending by category for selected time period (month, quarter, year)
- [ ] **RPT-02**: User can view spending trends by category over time (line chart or bar chart)
- [ ] **RPT-03**: User can view net worth (total assets minus total liabilities) as of specific date
- [ ] **RPT-04**: User can view net worth trend over time
- [ ] **RPT-05**: User can view account balances across all accounts
- [ ] **RPT-06**: User can filter reports by date range, account, or category

### Migration

- [ ] **MIG-01**: System can import Quicken transaction history from QIF or QFX export
- [ ] **MIG-02**: System preserves starting balances from Quicken import
- [ ] **MIG-03**: System correctly imports transfer transactions from Quicken (maintains link between both sides)
- [ ] **MIG-04**: System imports attachment files linked to Quicken transactions
- [ ] **MIG-05**: System imports brokerage transactions from Quicken
- [ ] **MIG-06**: System handles cleanup of poorly-modeled Quicken investment transactions (e.g., options expiration)
- [ ] **MIG-07**: User can map Quicken categories to new category structure during import

### Architecture & Infrastructure

- [ ] **ARCH-01**: Domain layer has no dependencies on infrastructure layer (Clean Architecture)
- [ ] **ARCH-02**: Domain objects do not depend on SQLAlchemy or database (Data Mapper pattern)
- [ ] **ARCH-03**: REST API uses FastAPI with automatic OpenAPI spec generation
- [ ] **ARCH-04**: DTOs use Pydantic for validation and serialization
- [ ] **ARCH-05**: PostgreSQL database with Alembic migrations
- [ ] **ARCH-06**: Frontend uses React with TypeScript
- [ ] **ARCH-07**: Frontend uses TanStack Query or similar for API state management
- [ ] **ARCH-08**: Services are containerized with Dockerfile
- [ ] **ARCH-09**: Development environment uses devcontainers
- [ ] **ARCH-10**: External service secrets use Envoy sidecar (not environment variables in container)
- [ ] **ARCH-11**: System implements hexagonal architecture (ports & adapters) with clear boundaries
- [ ] **ARCH-12**: Domain model implements four bounded contexts: Accounts, Transactions, Budgeting, Bank Sync

### Observability

- [ ] **OBS-01**: All services instrumented with OpenTelemetry (OTel)
- [ ] **OBS-02**: System exports RED metrics (Rate, Errors, Duration) for all API endpoints
- [ ] **OBS-03**: System tracks Plaid sync success rate and error rate
- [ ] **OBS-04**: System tracks background job success/failure rate
- [ ] **OBS-05**: System tracks transaction import counts and errors
- [ ] **OBS-06**: Grafana dashboards display key operational metrics
- [ ] **OBS-07**: System logs all financial mutations with before/after values for audit trail

### Testing

- [ ] **TEST-01**: Domain layer has comprehensive unit tests
- [ ] **TEST-02**: Critical financial calculations have property-based tests (money arithmetic, balance calculations)
- [ ] **TEST-03**: Use cases have integration tests with test database
- [ ] **TEST-04**: API endpoints have integration tests
- [ ] **TEST-05**: UI has end-to-end tests using Playwright (headless browser)
- [ ] **TEST-06**: UI tests cover critical workflows: create account, record transaction, view budget
- [ ] **TEST-07**: Tests inject time/date for time-dependent logic (scheduled transactions, date queries)

### Web Interface

- [ ] **WEB-01**: User can access application via web browser
- [ ] **WEB-02**: User can authenticate with email and password
- [ ] **WEB-03**: User session persists across browser refresh
- [ ] **WEB-04**: User can log out
- [ ] **WEB-05**: UI is responsive and usable on desktop browsers
- [ ] **WEB-06**: UI displays loading states during API calls
- [ ] **WEB-07**: UI displays error messages for failed operations
- [ ] **WEB-08**: UI uses type-safe API client generated from OpenAPI spec

### REST API

- [ ] **API-01**: All endpoints require authentication via JWT or similar
- [ ] **API-02**: API returns proper HTTP status codes (200, 201, 400, 401, 404, 500)
- [ ] **API-03**: API validates request bodies using Pydantic schemas
- [ ] **API-04**: API provides OpenAPI documentation at /docs endpoint
- [ ] **API-05**: API implements pagination for list endpoints
- [ ] **API-06**: API implements filtering and sorting for transaction lists
- [ ] **API-07**: API rate limits requests to prevent abuse

## Nice-to-Have (v1)

Features that would enhance v1 but are not blocking for initial release:

- **AI-01**: System learns categorization rules from user corrections
- **AI-02**: System suggests categories for new transactions based on learned patterns
- **RECON-06**: System detects potential duplicate transactions
- **RECON-07**: System flags duplicate transactions for user review
- **PLAID-10**: User can connect brokerage account via Plaid
- **PLAID-11**: User can connect IRA/retirement account via Plaid
- **SCAN-01**: User can upload receipt image and system extracts transaction details
- **SCAN-02**: System auto-merges extracted receipt transaction with existing transaction
- **IMPORT-01**: User can import transactions from CSV file
- **IMPORT-02**: User can import transactions from PDF bank statement
- **INV-09**: System tracks portfolio value over time
- **INV-10**: System calculates ROI for investment accounts
- **INV-11**: System shows asset allocation breakdown
- **RPT-08**: User can export data to CSV format
- **TAX-01**: System generates capital gains report for tax filing

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Mobile & Multi-User

- **MOBILE-01**: iOS mobile app with full transaction management
- **MOBILE-02**: Android mobile app with full transaction management
- **MOBILE-03**: Mobile apps sync with web via REST API
- **USER-01**: User can share account access with partner
- **USER-02**: Multiple users can have separate logins to same household
- **USER-03**: Users can label transactions as "mine", "yours", "ours"

### Advanced Features

- **BUDG-09**: System suggests budget amounts based on historical spending
- **BUDG-10**: System suggests budget amounts based on scheduled transactions
- **RECON-08**: System detects transfers in downloaded transactions automatically
- **RECON-09**: System merges downloaded transactions with scheduled transactions automatically
- **INV-12**: System tracks capital gains per holding (short-term vs long-term)
- **INV-13**: System models ESPP share transactions with proper cost basis
- **INV-14**: System models stock options (exercise, expiration)
- **FORECAST-01**: System projects future net worth based on scheduled transactions
- **FORECAST-02**: System provides what-if scenarios for retirement planning
- **ALERT-01**: System sends alerts for low account balances
- **ALERT-02**: System sends alerts for large transactions
- **ALERT-03**: System sends alerts for upcoming bills
- **CLI-01**: User can access data via command-line interface
- **CLI-02**: CLI supports transaction queries and reports
- **AI-03**: User can query financial data conversationally via AI (MCP server or Claude Code skills)
- **AI-04**: User can create transactions conversationally via AI

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time transaction notifications | Creates complexity; batch sync is sufficient for personal finance |
| Automatic bill pay | Liability risk; users should initiate payments manually |
| Direct bank credential storage | Security nightmare; use OAuth (Plaid) only |
| GraphQL API | REST is simpler and sufficient for use cases |
| Social features / sharing budgets publicly | Not aligned with core value of personal/private finance |
| Cryptocurrency tracking | Different domain with unique complexities; defer until proven need |
| International multi-currency from day 1 | Complex edge cases; focus on single base currency initially |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (To be filled by roadmapper) | | |

**Coverage:**
- v1 requirements: TBD total
- Mapped to phases: TBD
- Unmapped: TBD

---
*Requirements defined: 2026-01-29*
*Last updated: 2026-01-29 after initial definition*
