# Phase 2: Account Domain - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can create, edit, delete, and view accounts of all supported types (checking, savings, credit card, loan, brokerage, IRA, rewards) with current and historical balance tracking. This phase establishes the Account aggregate as the foundation for transaction recording (Phase 3) and bank synchronization (Phase 6).

Accounts are created manually with user-provided details. Plaid-based account creation is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Account Types and Fields

**Supported types (fixed for Phase 2):**
- Checking, Savings, Credit Card, Loan, Brokerage, IRA, Rewards
- System should be architecturally extensible for future specialized types (HSA, 529) built on these core types with additional hooks/rules

**Required vs optional fields:**
- Type-dependent requirements: Credit cards require credit limit, loans require APR and term, basic accounts just need name
- Allows manual account creation not tied to institution/Plaid integration
- Full institution details supported: institution name, account number, credit limits, APRs, maturity dates (everything from statements)

**Account subtypes:**
- IRA subtypes: Traditional, Roth, SEP
- Loan subtypes: Mortgage, Auto, Personal
- Modeled as account subtype field for type-specific domain logic

**Value tracking:**
- Most accounts store Money values (with currency)
- Rewards accounts store value + unit (e.g., 50000 'Alaska Miles')
- Brokerage shows cash balance; holdings/securities come in later phase

**Currency:**
- Single currency per account (Money type from Phase 1 already supports this)

**Credit cards:**
- Store credit limit only
- Available credit calculated as (limit - balance)

**Temporal fields:**
- Opening date (user-provided or creation date)
- Optional closing date (set when account closed)
- For loans: term + due date (if applicable - line of credit wouldn't have one)
- Opening balance (starting balance when account created)

**Account status:**
- Active/Closed only (simple two-state model)
- Closed accounts stay in system for historical data but can't accept new transactions

**Organization:**
- Accounts grouped by type or institution
- Optional user-defined sort within groups

**Metadata:**
- Institution name (required) + optional details (website, phone, notes)
- Optional notes field for user comments
- Attachment support for statements, letters, etc.

**Audit fields:**
- Standard audit tracking: created_at, updated_at, created_by, updated_by

**No joint ownership:**
- Phase 2 does not track joint accounts or multi-user ownership
- Single owner per account

**No default account:**
- No concept of "default account" in Phase 2
- Users explicitly choose account for each operation

### Balance Tracking

**Current balance:**
- Calculated from transactions: balance = opening balance + sum of all transactions
- No cached balance field (Phase 3 implements transaction system)

**Historical balance:**
- Point-in-time calculation: query transactions up to any date
- No daily snapshots or pre-aggregation
- Flexible approach allows balance queries for any historical date

**Negative balances:**
- Type-dependent rules:
  - Checking/savings can go negative (overdraft scenarios)
  - Credit cards show positive balance (amount owed)
  - Loans decrease from principal amount

**Cleared vs pending:**
- Transaction clearing status deferred to Phase 3
- Phase 2 defines balance calculation approach only

### Security and Encryption

**Encrypted fields:**
- Account numbers only (encrypted storage, masked display showing last 4 digits)
- Other metadata (institution name, notes) stored in plain text for querying

**Routing numbers:**
- Deferred to Phase 6 (Bank Sync)
- Will come from Plaid integration

### Account Lifecycle

**Deletion rules:**
- Accounts with transactions: prevent deletion, show error
- User must close account instead (preserves financial history)
- Accounts without transactions: hard delete (permanent removal)

**Close operation:**
- Explicit close account operation
- Sets status=Closed and closing_date timestamp
- Prevents new transactions on closed accounts

**Reopen operation:**
- Closed accounts can be reopened
- Clears closing_date, sets status=Active
- Allows fixing mistakes or resuming use of old accounts

**Audit trail:**
- Account changes emit domain events via outbox pattern
- Events: AccountCreated, AccountUpdated, AccountClosed, AccountReopened, AccountDeleted
- Full audit trail without separate history table

**No merging:**
- Account merging/combining not supported in Phase 2
- Moving transactions between accounts is complex, deferred

### Claude's Discretion

- Bulk operations (delete/close multiple accounts) - likely defer to UI phase
- Exact attachment storage implementation
- Error message wording for validation failures
- Domain event payload structures (within outbox pattern)

</decisions>

<specifics>
## Specific Ideas

**Manual account creation flow:**
- Supports accounts not synced to institutions or where institution lacks Plaid integration
- Users can create "offline" accounts for cash, local credit unions, etc.

**Future extensibility:**
- Specialized types like HSA and 529 should be built on core types with additional hooks/rules
- Architecture should support layering behavior without changing core 7 types

</specifics>

<deferred>
## Deferred Ideas

**Phase 6 (Bank Sync):**
- Plaid integration for adding accounts from bank connections
- Routing number storage and management
- Account credential storage

**Later phases:**
- Interest rates (APY for savings, APR for loans/cards) tracking and calculation
- Cleared vs pending balance distinction
- Visual customization (account colors, icons)
- Default account designation
- Account merging/combining functionality
- Bulk account operations in domain layer

</deferred>

---

*Phase: 02-account-domain*
*Context gathered: 2026-01-30*
