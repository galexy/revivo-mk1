---
status: diagnosed
phase: 15-api-integration-validation
source: 15-01-SUMMARY.md, 15-02-SUMMARY.md, 15-03-SUMMARY.md, 15-04-SUMMARY.md, 15-05-SUMMARY.md, 15-06-SUMMARY.md, 15-07-SUMMARY.md, 15-08-SUMMARY.md
started: 2026-02-11T12:00:00Z
updated: 2026-02-11T22:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Empty State Welcome Screen
expected: When no accounts exist, the dashboard shows a centered Wallet icon with "Welcome to Personal Finance" heading and an "Add Your First Account" CTA button. No sidebar is visible.
result: pass

### 2. Create Checking Account via Wizard
expected: Clicking "Add Your First Account" (or Add Account button) opens a 4-step wizard modal. Step 1: select "Checking" account type. Step 2: enter account name and optional details. Step 3: enter opening balance (currency input auto-formats). Step 4: review all details. Clicking "Create Account" closes wizard and account appears in sidebar under "Cash" group.
result: issue
reported: "the darken modal view makes it impossible to read anything"
severity: major

### 3. Sidebar Account Grouping and Subtotals
expected: After creating accounts, sidebar shows them grouped by category (Cash, Credit, Loans, Investments, Rewards). Each group header shows the total balance for accounts in that group. Groups are collapsible (click header to expand/collapse).
result: pass

### 4. Create Credit Card with Type-Specific Fields
expected: Creating a credit card account shows a credit limit field in the details step. After creation, account appears under "Credit" group in sidebar with correct balance.
result: pass

### 5. Account Detail Page
expected: Clicking an account in the sidebar navigates to its detail page showing account name, type, balance, account ID, and opened date.
result: pass

### 6. Edit Account via Context Menu
expected: Hovering over an account in sidebar reveals Edit/Delete actions. Clicking Edit opens the wizard pre-filled with the account's current data. Account type selection is locked (cannot change type). After editing name or other fields and completing wizard, sidebar reflects the updated information.
result: pass
note: User flagged that editing via wizard is not natural UX. Recommend a different edit pattern in a future phase.

### 7. Delete Account via Type-to-Confirm
expected: Clicking Delete on an account opens a confirmation dialog. Delete button is disabled until user types the exact account name. Once typed correctly, Delete button enables. Clicking it removes the account from the sidebar.
result: pass

### 8. Multiple Account Types in Sidebar
expected: After creating accounts of different types (e.g., checking, credit card, loan), sidebar correctly groups each under its category with accurate per-group subtotals. Clicking between accounts navigates to their respective detail pages.
result: pass
note: Multi-group sidebar works for checking, savings, credit card. Loan creation blocked by APR bug (see Gaps).

## Summary

total: 8
passed: 7
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Wizard modal content is readable with clear visual hierarchy"
  status: failed
  reason: "User reported: the darken modal view makes it impossible to read anything"
  severity: major
  test: 2
  root_cause: "globals.css @theme block only registers font variables, not color variables. Tailwind v4 silently ignores all shadcn/ui semantic color utilities (bg-background, text-foreground, etc.) so DialogContent has no background color — it is transparent."
  artifacts:
    - path: "apps/web/src/styles/globals.css"
      issue: "@theme block missing --color-* mappings; :root color values use raw HSL components without hsl() wrapper"
  missing:
    - "Wrap :root color values in hsl() for complete color values"
    - "Add @theme inline block mapping --color-background, --color-foreground, etc. to CSS variables"
  debug_session: ".planning/debug/dialog-overlay-bleed.md"

- truth: "Loan accounts can be created via wizard with APR percentage input"
  status: failed
  reason: "API returns 422: APR field validates <= 1 (expects decimal like 0.065) but UI sends percentage (6.5)"
  severity: major
  test: 8
  root_cause: "useCreateAccount hook sends formData.apr raw without dividing by 100. UI label says 'APR (%)' but no conversion from percentage to decimal fraction before API call."
  artifacts:
    - path: "apps/web/src/features/accounts/hooks/useCreateAccount.ts"
      issue: "Line 67: sends apr as-is without / 100 conversion"
    - path: "apps/web/src/features/accounts/validation/accountSchemas.ts"
      issue: "APR field is z.string().optional() with no numeric range validation"
    - path: "apps/web/src/components/accounts/AccountWizard.tsx"
      issue: "Line 80: edit mode populates apr from API without * 100 conversion back to percentage"
  missing:
    - "Convert APR from percentage to decimal in useCreateAccount before sending (6.5 -> 0.065)"
    - "Add 0-100 range validation in accountSchemas.ts Zod schema"
    - "Convert API decimal back to percentage in edit mode form population"
  debug_session: ".planning/debug/apr-mismatch-loan.md"
