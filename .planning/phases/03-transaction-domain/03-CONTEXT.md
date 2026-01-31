# Phase 3: Transaction Domain - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Record financial transactions with categories, splits, and transfers between accounts. Users can create, edit, and delete transactions. Transactions support split categorization and transfers between accounts update both account balances. Search, filtering, and basic CRUD operations are in scope. Attachments are deferred to a later phase.

</domain>

<decisions>
## Implementation Decisions

### Transaction Structure
- Every transaction has 1+ split lines (even single-category transactions have one split)
- Transaction amount = net flow to account (positive = inflow, negative = outflow)
- Split amounts are signed (positive = income/inflow, negative = expense/outflow)
- All splits must sum exactly to the transaction amount — system validates
- Unlimited split lines allowed per transaction
- Each split line can have its own memo

### Transfer Splits
- Transfer splits can only be outgoing (negative amount, money leaving source account)
- Mirror transactions are always incoming (positive amount, no splits allowed on mirrors)
- Source account "owns" the transfer; mirror is a derived record
- Mirror transactions created automatically when transfer split is added
- Mirror transactions deleted when transfer split is removed (orphan any matched downloaded transactions)
- Mirrors inherit memo from source (not independent)
- Can add transfer splits after transaction creation; fully editable
- Validation: prevent circular transfers (A→B→A in same transaction)
- Validation: prevent self-transfer (split targeting own account)
- Validation: cannot transfer to closed/deleted accounts
- A transaction can consist entirely of transfer splits (pure transfer, no categories)
- Mixed transactions allowed: category splits + transfer splits together, all must sum to transaction amount

### Dates
- All transactions have both effective date and posted date
- Effective date = when transaction logically occurred (check date, purchase date)
- Posted date = when it cleared/appeared in account
- Manual entry default: posted date = effective date (user can change)
- Balance calculations: user choice per view (posted-based vs effective-based)
- For transfers: effective date syncs between source and mirror; posted dates are independent

### Transfer Edit Propagation
- Edits to source transaction propagate to mirror (amount, effective date, memo)
- Mirror's posted date is independent (can differ from source)
- If mirror has been matched to a downloaded transaction, warn user but allow edit

### Transaction Status
- Status progression: Pending → Cleared → Reconciled
- Reconciled transactions: warn when editing, but allow it
- Status applies to the transaction as a whole

### Transaction Fields
- Check number: optional field for paper check tracking
- Payees: managed entity list with autocomplete
- New payees auto-created when entering transactions (type new name = creates payee)

### Categories
- Hierarchical structure (parent/child categories)
- Transactions can be assigned to any level (parent or leaf)
- System category: "Uncategorized" — always exists, cannot be modified or deleted
- Transfer: meta-category (special handling — split targets account, not category)
- User categories: fully manageable (create, rename, delete, reorganize)

### Downloaded Transactions (Foundation for Phase 6)
- Transactions track source: manual vs downloaded (may be distinct subtypes)
- Downloaded transactions can exist standalone without being linked
- Downloaded transactions can be fully categorized with splits (same as manual)
- Linking model: manual + downloaded are separate records, linked together
- When linked: shown as single line item in UI; user can unlink
- Unlinking restores both as independent transactions
- Field precedence when linked:
  - From downloaded: amount, posted date
  - From manual: effective date, category, memo, splits
- If both have splits when linking: manual splits win
- Link captures snapshot of downloaded transaction at link time (not manual)
- Deleting transaction with linked download: detach and orphan the downloaded transaction

### Rewards Handling
- Rewards earning within a transaction: Claude's discretion on modeling approach
- Rewards redemption: can be done via split
- Redemption entry: user specifies both points redeemed AND dollar value received
- System can calculate effective redemption rate from those values

### Claude's Discretion
- Payee default category for auto-fill
- Category hierarchy depth (two levels vs unlimited)
- Downloaded transaction type structure (single type with discriminator vs subtypes)
- Rewards earning model (zero-value split, metadata, or separate transaction)
- Transfer split structure in API (category OR account field vs distinct split type)

</decisions>

<specifics>
## Specific Ideas

- Transfers should feel atomic — user creates one entry, system handles both sides
- The split model enables Quicken-style split transactions while being more flexible
- Downloaded transaction linking preserves audit trail — both records exist, linkage is explicit
- "If they're linked and I edit, warn me" — don't silently propagate changes that might conflict with bank data

</specifics>

<deferred>
## Deferred Ideas

- **Attachments bounded context** — Separate service for file storage (S3-based), transactions will reference by ID. Fully deferred from Phase 3.
- **Multi-currency support** — Transfers between accounts with different currencies, exchange rate tracking
- **Starter categories** — Pre-populated common categories (would be normal user categories, not system-protected)

</deferred>

---

*Phase: 03-transaction-domain*
*Context gathered: 2026-01-31*
