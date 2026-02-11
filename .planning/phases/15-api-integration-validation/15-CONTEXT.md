# Phase 15: API Integration Validation - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate frontend-backend integration by building account CRUD through the UI. Users can create, edit, and delete accounts via a wizard-style modal. Transaction UI is explicitly out of scope (Phase 17).

**Rescoped from original roadmap:** Original Phase 15 included both account and transaction CRUD. User decision: focus this phase on accounts only. Transaction CRUD deferred to Phase 17.

</domain>

<decisions>
## Implementation Decisions

### Account wizard flow
- 4-step wizard in a **dialog/modal**: Account Type -> Name & Details -> Opening Balance -> Review & Confirm
- All account types shown in step 1 (checking, savings, credit card, loan, brokerage, IRA, rewards) -- no hidden types
- **Step dots/progress bar** at top of modal showing current step (not named steps)
- Offline accounts only -- no institution connection flow

### Account list & sidebar
- Accounts displayed in the **left sidebar**, grouped by type category (Cash, Credit, Loans, Investments, Rewards)
- Each account shows **name + balance**
- Group headers show **subtotal balance** for that category
- Clicking an account navigates to its detail view (empty transaction list for now)

### Edit & delete
- Edit reuses the **same wizard modal**, pre-filled with current values
- Account type is **locked after creation** (not editable) -- may allow in future
- Delete requires **type-to-confirm** (user must type account name)
- Edit and delete accessible via **sidebar context menu** (right-click or ... menu)

### Empty state & first run
- Zero accounts: **centered welcome prompt** with illustration and prominent "Add your first account" button
- Welcome message stays focused on accounts only -- no roadmap teasing
- After first account creation: navigate to the **account detail view** (shows account name/balance, empty transaction list)

### Component & design strategy
- New shadcn/ui components needed: Dialog, Select, RadioGroup, Separator, Badge
- **Each view gets a dedicated design task** (visual-first) that:
  - Uses the `frontend-design` skill for high-quality visual output
  - Researches existing shadcn/ui components before implementation
  - Focuses on visual design and layout, not functionality
- Functionality implementation follows as a separate task after design is approved

### Claude's Discretion
- Exact wizard step content layout and spacing
- Account type icons/visual treatment in the type selection step
- Sidebar collapse/expand behavior
- Illustration choice for empty state
- Loading states and animation transitions between wizard steps
- Currency input formatting in the balance step

</decisions>

<specifics>
## Specific Ideas

- Wizard should feel lightweight despite having 4 steps -- modern finance apps (Monarch, YNAB, Lunch Money) keep account creation fast and focused
- Sidebar account list follows YNAB-style pattern: grouped accounts with balances, always visible
- Type-to-confirm delete pattern for account deletion (prevents accidental data loss)
- Design-first approach: each view should be visually polished before wiring up API calls

</specifics>

<deferred>
## Deferred Ideas

- Transaction CRUD via UI -- Phase 17 (explicitly removed from Phase 15 scope)
- Institution connection / linked accounts -- Phase 22 (Bank Sync)
- Changing account type after creation -- future enhancement
- Account detail page with edit/delete buttons (currently sidebar context menu only) -- revisit when account detail page gets richer content

</deferred>

---

*Phase: 15-api-integration-validation*
*Context gathered: 2026-02-11*
