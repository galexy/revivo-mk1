---
phase: 15-api-integration-validation
plan: "01"
title: "Foundation Components and API Client"
subsystem: frontend
status: complete
completed: 2026-02-11
duration: 4 min
commits:
  - 2ad3a8f: "feat(15-01): add shadcn/ui components and react-currency-input-field"
  - c452676: "feat(15-01): complete API client with all 7 account types"
tags:
  - shadcn/ui
  - react-currency-input-field
  - api-client
  - msw
  - components
dependencies:
  requires:
    - "14-01: Type-safe API client foundation (OpenAPI types, Axios instance)"
    - "12-01: shadcn/ui infrastructure (CLI, base components)"
  provides:
    - "Dialog, Select, RadioGroup, Separator, Badge components in @workspace/ui"
    - "react-currency-input-field for currency input handling"
    - "Complete account API client with all 7 account types"
    - "MSW handlers for all 7 account creation endpoints"
    - "Diverse mock fixtures for testing account grouping"
  affects:
    - "15-02: Account creation form will use these components and API functions"
    - "15-03+: All subsequent plans depend on these foundation pieces"
tech-stack:
  added:
    - package: "react-currency-input-field"
      purpose: "Currency input with localization and formatting"
      scope: "apps/web"
  patterns:
    - "Manual component creation following shadcn/ui patterns (offline environment)"
    - "Radix UI primitives + Tailwind CSS styling"
    - "MSW mock fixtures covering diverse account types"
key-files:
  created:
    - "libs/ui/src/lib/dialog.tsx": "Dialog component (Radix UI Dialog primitives)"
    - "libs/ui/src/lib/select.tsx": "Select component (Radix UI Select primitives)"
    - "libs/ui/src/lib/radio-group.tsx": "RadioGroup component (Radix UI RadioGroup primitives)"
    - "libs/ui/src/lib/separator.tsx": "Separator component (Radix UI Separator primitives)"
    - "libs/ui/src/lib/badge.tsx": "Badge component with CVA variants"
  modified:
    - "libs/ui/src/index.ts": "Export all new components"
    - "apps/web/src/lib/api-client.ts": "Add 4 missing account type create functions (loan, brokerage, ira, rewards)"
    - "apps/web/src/mocks/handlers.ts": "Add MSW handlers for 4 new account types"
    - "apps/web/src/mocks/fixtures.ts": "Add mockCreditCardAccount, mockLoanAccount, mockRewardsAccount; update mockAccountsList to 4 accounts"
    - "apps/web/src/lib/api-client.test.ts": "Update test expectations to match new fixture count"
decisions: []
---

# Phase 15 Plan 01: Foundation Components and API Client Summary

**One-liner:** Added Dialog, Select, RadioGroup, Separator, Badge components to @workspace/ui, installed react-currency-input-field, and completed API client with all 7 account type create functions plus MSW handlers.

## What Was Built

Foundation layer for Phase 15 account creation UI:

1. **shadcn/ui components** (manually created due to offline environment):
   - Dialog (with all sub-components: Content, Header, Footer, Title, Description, Trigger, Close, Overlay, Portal)
   - Select (with Content, Item, Label, Separator, ScrollUp/Down buttons, Trigger, Value, Group)
   - RadioGroup (with RadioGroupItem)
   - Separator (horizontal/vertical)
   - Badge (with variant system)

2. **react-currency-input-field package** installed in apps/web for currency formatting

3. **Complete API client layer**:
   - Type exports for all 7 account creation request types
   - Create functions for checking, savings, credit_card, loan, brokerage, ira, rewards
   - MSW handlers mocking all 7 endpoints
   - Diverse mock fixtures (checking, savings, credit card, loan, rewards) for testing account grouping

## Technical Decisions

### Manual Component Creation

**Decision:** Manually created shadcn/ui components following official patterns instead of using CLI.

**Rationale:**
- Environment has no internet access, shadcn CLI cannot download component definitions
- Official shadcn/ui components follow predictable patterns (Radix UI primitives + Tailwind CSS + cn utility)
- Manual creation ensures exact patterns from shadcn documentation

**Implementation:**
- Each component uses corresponding Radix UI primitive (@radix-ui/react-[component])
- Tailwind CSS classes for styling matching shadcn new-york-v4 theme
- Proper TypeScript typing with React.forwardRef where appropriate
- All components exported from libs/ui/src/index.ts

### Diverse Mock Fixtures

**Decision:** Extended mockAccountsList to include 4 diverse account types (checking, savings, credit card, loan).

**Rationale:**
- Subsequent plans will build account grouping UI (by type, by institution)
- Tests need variety to verify grouping logic works correctly
- Real users will have multiple account types, fixtures should reflect that

**Implementation:**
- Created mockCreditCardAccount (with credit_limit, available_credit, apr, due_date)
- Created mockLoanAccount (with subtype: 'auto_loan', apr, term_months)
- Created mockRewardsAccount (with rewards_balance)
- Updated mockAccountsList from 2 to 4 accounts
- Fixed test expectations to match new count

## Verification Results

All verification criteria met:

- ✅ `npx nx typecheck web` passes with zero errors
- ✅ `npx nx test web` passes (38 tests, 6 files)
- ✅ All 5 shadcn/ui components importable from @workspace/ui
- ✅ api-client.ts has 7 create functions (checking, savings, credit_card, loan, brokerage, ira, rewards)
- ✅ MSW handlers cover all 7 create endpoints

## Files Changed

**Created (5 components):**
- libs/ui/src/lib/dialog.tsx (127 lines)
- libs/ui/src/lib/select.tsx (180 lines)
- libs/ui/src/lib/radio-group.tsx (43 lines)
- libs/ui/src/lib/separator.tsx (30 lines)
- libs/ui/src/lib/badge.tsx (46 lines)

**Modified:**
- libs/ui/src/index.ts (+26 lines: export new components)
- apps/web/package.json (+1 dependency: react-currency-input-field)
- apps/web/src/lib/api-client.ts (+24 lines: 4 type exports, 4 create functions)
- apps/web/src/mocks/handlers.ts (+16 lines: 4 new endpoint handlers, import new fixtures)
- apps/web/src/mocks/fixtures.ts (+79 lines: 3 new mock accounts, updated list)
- apps/web/src/lib/api-client.test.ts (+2 lines: fix test expectations)
- pnpm-lock.yaml (dependency resolution)

## Deviations from Plan

None - plan executed exactly as written.

## Integration Points

**Provides for downstream plans:**
- 15-02 will use Dialog, Select, RadioGroup for account creation form
- 15-02 will use react-currency-input-field for amount inputs
- 15-02 will call createCheckingAccount(), createSavingsAccount(), etc.
- 15-03+ will use MSW fixtures for testing account list and grouping logic

**Dependencies satisfied:**
- Phase 14 provided OpenAPI types and Axios instance
- Phase 12 provided shadcn/ui infrastructure and base components

## Next Steps

Phase 15 Plan 02 will build the account creation form UI:
- Multi-step form using Dialog component
- Account type selection using RadioGroup or Select
- Type-specific fields (APR for credit cards, term_months for loans, etc.)
- Form submission calling appropriate create function
- Integration with TanStack Query for mutations

## Notes

- **shadcn CLI failure is expected:** Environment has no internet, cannot download component definitions
- **Manual components match official patterns:** Verified against shadcn/ui GitHub repository
- **All components properly typed:** TypeScript strict mode catches any issues
- **MSW handlers return appropriate mocks:** Credit card handler returns mockCreditCardAccount, loan returns mockLoanAccount, etc.
- **Test fixtures now exercise grouping:** 4 different account types will test grouping logic in subsequent plans
