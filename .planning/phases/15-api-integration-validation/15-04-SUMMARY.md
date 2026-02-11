---
phase: 15-api-integration-validation
plan: 04
subsystem: ui
tags: [react, tanstack-query, tanstack-router, crud, accounts]

# Dependency graph
requires:
  - phase: 15-02
    provides: EmptyAccountsState, AccountSidebar, account grouping components
  - phase: 15-03
    provides: AccountWizard, DeleteAccountDialog, validation schemas
  - phase: 15-01
    provides: API client functions, MSW handlers, query setup
provides:
  - TanStack Query mutation hooks for account CRUD (create, update, delete)
  - useAccounts convenience hook for fetching account list
  - DashboardPage with real API data and full CRUD integration
  - Account detail route with navigation support
  - Empty state handling for zero accounts
affects: [15-05, 15-06, 15-07, transaction-features, dashboard-improvements]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TanStack Query mutation hooks with cache invalidation"
    - "Router navigation in sidebar components via useNavigate"
    - "Conditional rendering based on account count (empty state vs sidebar)"

key-files:
  created:
    - apps/web/src/features/accounts/hooks/useAccounts.ts
    - apps/web/src/features/accounts/hooks/useCreateAccount.ts
    - apps/web/src/features/accounts/hooks/useUpdateAccount.ts
    - apps/web/src/features/accounts/hooks/useDeleteAccount.ts
    - apps/web/src/pages/AccountDetailPage.tsx
  modified:
    - apps/web/src/pages/DashboardPage.tsx
    - apps/web/src/features/accounts/components/AccountSidebar.tsx
    - apps/web/src/routes.tsx
    - apps/web/src/app/App.test.tsx

key-decisions:
  - "API accepts amount as number | string, passed form values directly without parseFloat"
  - "Rewards accounts use rewards_balance with value/unit, not opening_balance"
  - "useCreateAccount maps wizard formData to type-specific API request shapes via switch statement"
  - "Account detail route is nested under dashboard for layout inheritance"
  - "Test wrapped with QueryClientProvider to provide TanStack Query context"

patterns-established:
  - "Mutation hooks return useMutation with onSettled cache invalidation"
  - "useAccounts unwraps AccountListResponse.accounts array for convenience"
  - "AccountSidebar uses router params to detect active account for highlighting"

# Metrics
duration: 6min
completed: 2026-02-11
---

# Phase 15 Plan 04: Account CRUD Integration Summary

**TanStack Query mutation hooks wire AccountWizard and DeleteAccountDialog to real API, enabling full CRUD with cache invalidation and account detail navigation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-11T19:53:03Z
- **Completed:** 2026-02-11T19:58:54Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Four mutation hooks (useAccounts, useCreateAccount, useUpdateAccount, useDeleteAccount) handle all account CRUD operations
- DashboardPage shows EmptyAccountsState for zero accounts, AccountSidebar with real data when accounts exist
- Clicking account in sidebar navigates to detail view with account info and balance
- Creating/editing/deleting accounts updates sidebar immediately via TanStack Query cache invalidation
- All tests pass including App.test.tsx with QueryClientProvider wrapper

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TanStack Query mutation hooks for account CRUD** - `3fcc955` (feat)
2. **Task 2: Rewire DashboardPage with real data, routing, and CRUD integration** - `ea8a197` (feat)

## Files Created/Modified
- `apps/web/src/features/accounts/hooks/useAccounts.ts` - Convenience hook for fetching accounts list
- `apps/web/src/features/accounts/hooks/useCreateAccount.ts` - Maps wizard formData to type-specific create API calls
- `apps/web/src/features/accounts/hooks/useUpdateAccount.ts` - Updates account with cache invalidation
- `apps/web/src/features/accounts/hooks/useDeleteAccount.ts` - Deletes account and removes from cache
- `apps/web/src/pages/DashboardPage.tsx` - Rewired with useAccounts, wizard state, delete dialog state, empty state handling
- `apps/web/src/pages/AccountDetailPage.tsx` - Account detail page showing account info and balance
- `apps/web/src/features/accounts/components/AccountSidebar.tsx` - Updated to navigate on click via useNavigate
- `apps/web/src/routes.tsx` - Added account detail route nested under dashboard
- `apps/web/src/app/App.test.tsx` - Wrapped RouterProvider with QueryClientProvider for test context

## Decisions Made

**API type handling:**
- Discovered API accepts amount as `number | string` (MoneySchema-Input)
- Passed form string values directly without parseFloat for type safety
- Rewards accounts use `rewards_balance` with `value/unit`, not `opening_balance` with `amount/currency`

**Mutation hook design:**
- useCreateAccount uses switch statement to map accountType to correct API function
- Each account type constructs type-specific request payload (e.g., credit_card adds credit_limit, loan adds apr/term_months)
- onSettled invalidates queryKeys.accounts.lists() for all mutations
- useDeleteAccount also removeQueries for the specific account detail

**Routing strategy:**
- Account detail route `/dashboard/accounts/$accountId` nested under dashboard for layout inheritance
- AccountSidebar uses useParams to detect active account from route params
- Navigate to detail view on account click, not just select state

**Test setup:**
- Tests required QueryClientProvider wrapper around RouterProvider
- Mocked api.get to return empty accounts list `{ data: { accounts: [] } }`
- Changed assertion to `welcome to personal finance` to avoid multiple "Personal Finance" matches

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Type errors on first typecheck:**
- Issue: API expected amount as string, but code used parseFloat
- Resolution: Checked MoneySchema-Input type definition, found it accepts `number | string`, passed form values directly
- Files: useCreateAccount.ts fixed to use string values without parsing

**Rewards account structure:**
- Issue: rewards_balance has value/unit structure, not amount/currency like MoneySchema
- Resolution: Checked RewardsBalanceSchema-Input type, adjusted useCreateAccount to use correct fields
- Files: useCreateAccount.ts case 'rewards' block

**Test failures:**
- Issue: DashboardPage uses useAccounts hook requiring QueryClient, but test didn't provide QueryClientProvider
- Resolution: Wrapped RouterProvider with QueryClientProvider in both test cases
- Files: App.test.tsx

**Multiple "Personal Finance" matches:**
- Issue: Test failed with "Found multiple elements with text: /personal finance/i" (header + empty state)
- Resolution: Changed assertion to search for "welcome to personal finance" (unique to empty state)
- Files: App.test.tsx

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Full account CRUD functional with real API integration
- Ready for transaction features and advanced account operations
- Account detail page is placeholder - will be enhanced in future phases
- Sidebar navigation and empty state handling complete

---
*Phase: 15-api-integration-validation*
*Completed: 2026-02-11*
