# Personal Finance Platform

## What This Is

A modern personal finance application that provides data sovereignty and proper domain modeling of real-world financial transactions. Built to replace Quicken with support for multiple interfaces (web UI, API, CLI, AI), comprehensive account type support, intelligent reconciliation, and envelope budgeting. Designed using Domain-Driven Design and Clean Architecture principles with observability built in from day 1.

## Core Value

Own your financial data and access it anywhere through any interface - web, API, CLI, or AI. Your data, your tools, no vendor lock-in.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Account Management:**
- [ ] Support multiple account types: checking, savings, credit cards, loans/mortgages, brokerage (equity), IRA/retirement, miles/rewards accounts
- [ ] Create and manage accounts with starting balances
- [ ] Track current account balances

**Transaction Management:**
- [ ] Record transactions manually
- [ ] Import transactions via Plaid (checking and credit card accounts)
- [ ] Transaction categories with split category support
- [ ] Transfers between accounts (proper domain modeling)
- [ ] Scheduled/recurring transactions that auto-create instances
- [ ] Manually record next scheduled transaction
- [ ] Merge downloaded transactions with manual entries
- [ ] Merge downloaded transactions with scheduled transactions
- [ ] Merge downloaded transactions that are actually transfers
- [ ] Attach receipts/invoices to transactions
- [ ] Intelligent payee/payer renaming
- [ ] Auto-categorize transactions based on historical patterns

**Investment Tracking:**
- [ ] Investment transaction history (buy, sell, dividend, options, ESPP)
- [ ] Cost basis tracking
- [ ] Capital gains tracking (short-term and long-term)
- [ ] Proper modeling of complex transactions (options expiration, ESPP shares)

**Complex Transaction Modeling:**
- [ ] Split transactions (part payment, part transfer)
- [ ] Mortgage payments (principal → equity/loan paydown, interest → expense)
- [ ] Multi-leg transactions with proper domain representation

**Budgeting:**
- [ ] Flexible envelope budgeting for one year
- [ ] Smart budget suggestions based on historical spending
- [ ] Budget suggestions based on scheduled transactions
- [ ] Track spending against budget by category

**Reporting & Views:**
- [ ] Spending by category over time
- [ ] Account balance views
- [ ] Transaction history with filtering
- [ ] Net worth calculation (assets - liabilities)

**Migration:**
- [ ] Import from Quicken: transaction history with starting balances
- [ ] Import from Quicken: transfers between accounts (preserve relationships)
- [ ] Import from Quicken: attachments on transactions
- [ ] Import from Quicken: brokerage transactions (with cleanup for poorly-modeled primitives)

**Interfaces:**
- [ ] Web UI (React + TypeScript)
- [ ] REST API with OpenAPI spec

**Architecture & Testing:**
- [ ] DDD + Clean Architecture implementation (dependencies flow inward)
- [ ] Domain layer with no storage dependencies
- [ ] Domain tests
- [ ] Integration tests
- [ ] UI tests (Playwright or Chrome DevTools MCP, headless browser)

**Observability:**
- [ ] OpenTelemetry instrumentation
- [ ] RED metrics (Rate, Errors, Duration)
- [ ] Grafana dashboards for operational monitoring
- [ ] Track: Plaid sync success rate, API response times, transaction import errors, background job success/failure

**Nice-to-Have (v1):**
- [ ] AI-powered categorization learning (user corrects, AI induces rules)
- [ ] Duplicate transaction detection
- [ ] Plaid sync for brokerage/retirement accounts
- [ ] Portfolio value tracking over time
- [ ] Investment performance metrics (ROI, allocation)
- [ ] Bank/brokerage statement import (CSV/PDF)
- [ ] Capital gains tax reports
- [ ] Receipt scanning and auto-merge
- [ ] CLI interface

### Out of Scope

- Mobile app — Web-first, mobile is v2+
- Multi-user support — Single user (plus manual sharing), multi-tenant is future
- Retirement forecasting and what-if scenarios — Budgeting for one year only in v1
- Alerts and notifications — Not a priority for v1
- Data export (CSV/JSON) — Not needed for v1
- Automatic recurring subscription detection — Future enhancement
- GraphQL API — Using REST only
- Active Record pattern — Using Data Mapper to preserve domain independence

## Context

**Current State:**
- Currently using Quicken, frustrated with lack of innovation over the years
- Features from Microsoft Money (early 2000s) like configurable budgeting still not available in modern Quicken
- Need to migrate complete transaction history including transfers and attachments

**Key Pain Points Being Solved:**
- Poor modeling of real-world transactions: ESPP shares, options expiration, complex mortgage payments not treated as first-class concepts
- Dumb transaction reconciliation: Quicken poorly merges scheduled with downloaded transactions
- Vendor lock-in: Cannot access data via API, CLI, or AI tools
- Limited budgeting: Want envelope budgeting with smart suggestions

**Domain Complexity:**
- Transfers are not simple transactions - they affect two accounts with no expense category
- Downloaded transactions must be intelligently matched to identify transfers vs payments
- Split transactions can combine payment and transfer (mortgage: principal = transfer to equity, interest = expense)
- Investment transactions have complex primitives (options, ESPP) that need proper domain modeling

**User Behavior:**
- Takes pictures of most receipts - want to attach to transactions
- Has multiple Fidelity accounts (willing to move for better Plaid support)
- Currently shares Quicken file with partner manually

## Constraints

- **Architecture**: DDD + Clean Architecture (hexagonal/onion architecture) — dependencies MUST flow from outer layers toward inner layers only. Domain layer cannot depend on infrastructure or application layers.
- **Data Access Pattern**: Data Mapper pattern (NOT Active Record) — domain objects must not depend on storage mechanisms. This is critical to Clean Architecture compliance.
- **Backend Language**: Python
- **Backend Framework**: REST API with Python type support for OpenAPI generation (e.g., FastAPI)
- **DTOs**: Pydantic for data transfer objects and marshalling across layers
- **Database**: PostgreSQL with SQLAlchemy using Data Mapper pattern
- **Frontend**: React with TypeScript
- **API Style**: REST (not GraphQL)
- **State Management**: Use established React state/sync library (React Query, SWR, or similar) - do not hand-roll
- **Observability**: OpenTelemetry (OTel) for instrumentation
- **Deployment**: Kubernetes (K8s) as deployment target
- **Containerization**: Services must be containerized
- **Development Environment**: Devcontainers
- **Secret Management**: Envoy proxy sidecar for external service secrets (no secrets visible in containers)
- **Testing**: Domain, integration, and UI tests are mandatory for v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Plaid for bank sync | Avoid direct integration with hundreds of financial institutions | — Pending |
| Data Mapper over Active Record | Preserve domain independence, enable Clean Architecture | — Pending |
| Envoy sidecar for secrets | Keep secrets out of container environment variables | — Pending |
| REST over GraphQL | Simpler for multi-interface access, well-understood patterns | — Pending |
| Python + FastAPI | Type safety, OpenAPI generation, strong ecosystem | — Pending |
| React state management library | Avoid reinventing solved problems, battle-tested solutions | — Pending |
| K8s deployment | Production-grade orchestration, observability integration | — Pending |
| OTel from day 1 | Observability as foundational requirement, not afterthought (SRE mindset) | — Pending |

---
*Last updated: 2026-01-29 after initialization*
