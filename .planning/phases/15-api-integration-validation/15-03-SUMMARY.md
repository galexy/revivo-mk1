---
phase: 15
plan: 03
subsystem: frontend-forms
tags: [react, wizard, forms, zod, react-hook-form, shadcn-ui]
requires: [15-01]
provides:
  - account-wizard-modal
  - delete-confirmation-dialog
  - multi-step-form-validation
  - type-specific-form-fields
affects: [15-04, 15-05]
tech-stack:
  added: []
  patterns:
    - multi-step-form-with-per-step-validation
    - type-to-confirm-delete-pattern
    - controlled-dialog-with-state-reset
key-files:
  created:
    - apps/web/src/features/accounts/validation/accountSchemas.ts
    - apps/web/src/features/accounts/components/ProgressDots.tsx
    - apps/web/src/features/accounts/components/AccountWizardSteps/StepTypeSelection.tsx
    - apps/web/src/features/accounts/components/AccountWizardSteps/StepDetails.tsx
    - apps/web/src/features/accounts/components/AccountWizardSteps/StepOpeningBalance.tsx
    - apps/web/src/features/accounts/components/AccountWizardSteps/StepReview.tsx
    - apps/web/src/features/accounts/components/AccountWizard.tsx
    - apps/web/src/features/accounts/components/DeleteAccountDialog.tsx
  modified: []
decisions:
  - id: per-step-zod-schemas
    choice: Separate Zod schema for each wizard step
    rationale: Progressive validation - each step validates independently, cleaner than monolithic schema
  - id: progress-dots-not-bar
    choice: Dots indicator instead of progress bar
    rationale: 4 steps is small count, dots are clearer than percentage bar
  - id: controlled-dialog-pattern
    choice: Controlled Dialog with useEffect reset on close
    rationale: Prevents stale form data across open/close cycles (Radix Dialog doesn't unmount on close)
  - id: type-specific-fields
    choice: Conditional rendering based on accountType
    rationale: Credit cards need credit_limit, loans need apr/term/subtype, IRAs need subtype, rewards need rewardsUnit
  - id: edit-mode-via-prop
    choice: Single AccountWizard component handles both create and edit via optional editAccount prop
    rationale: Avoid duplicating 4-step logic, pre-fill form data in useEffect when editAccount exists
  - id: type-to-confirm-delete
    choice: User must type exact account name to enable delete button
    rationale: Prevents accidental data loss, standard pattern for destructive actions
  - id: currency-input-library
    choice: react-currency-input-field for monetary inputs
    rationale: Handles locale formatting, decimal limits, prefix/suffix - harder than it looks
metrics:
  duration: "~5 min"
  completed: 2026-02-11
---

# Phase 15 Plan 03: Account Wizard and Delete Dialog Design Summary

4-step account wizard modal and type-to-confirm delete dialog using Zod validation, React Hook Form, and shadcn/ui Dialog components.

## What Was Built

**Account Wizard Modal (4 steps):**
1. **Step 1 - Type Selection:** Radio cards for all 7 account types (checking, savings, credit_card, loan, brokerage, ira, rewards) with Lucide icons and descriptions
2. **Step 2 - Details:** Account name + type-specific fields (credit_limit for credit cards, apr/term/subtype for loans, subtype for IRAs, rewardsUnit for rewards)
3. **Step 3 - Opening Balance:** Currency input (react-currency-input-field) for monetary accounts, plain number input for rewards
4. **Step 4 - Review:** Read-only summary of all entered data with formatted display

**Delete Confirmation Dialog:**
- Type-to-confirm pattern: user must type exact account name to enable delete button
- Destructive button variant disabled until confirmation matches
- State reset on dialog close via useEffect

**Validation Infrastructure:**
- Per-step Zod schemas (stepTypeSchema, stepDetailsSchema, stepBalanceSchema, stepReviewSchema)
- AccountFormData type for merged form data
- Progressive validation - each step validates independently before advancing

**Progress Indicator:**
- ProgressDots component with accessible ARIA attributes
- Shows current step (filled), completed steps (semi-transparent), future steps (muted)

## Technical Approach

**Multi-Step Form Pattern:**
```typescript
// Per-step validation with zodResolver
const form = useForm({
  resolver: zodResolver(stepSchemas[currentStep]) as any,
  defaultValues: formData,
  mode: 'onChange',
});

// Advance only if current step is valid
const goToNextStep = async () => {
  const isValid = await form.trigger();
  if (isValid) {
    setFormData({ ...formData, ...form.getValues() });
    setCurrentStep((prev) => Math.min(prev + 1, stepSchemas.length - 1));
    form.clearErrors();
  }
};
```

**Controlled Dialog with Reset:**
```typescript
// CRITICAL: Reset form when dialog closes (Radix Dialog hides but doesn't unmount)
useEffect(() => {
  if (!open) {
    setCurrentStep(0);
    setFormData({});
    form.reset();
    setIsSubmitting(false);
  }
}, [open, form]);
```

**Edit Mode Support:**
```typescript
// Populate form data from editAccount prop
useEffect(() => {
  if (editAccount && open) {
    const editData: Partial<AccountFormData> = {
      accountType: editAccount.account_type as any,
      name: editAccount.name,
      openingBalance: editAccount.current_balance.amount,
      // ... type-specific fields
    };
    setFormData(editData);
    form.reset(editData);
  }
}, [editAccount, open, form]);
```

**Type-Specific Fields:**
- Credit Card: `creditLimit` (currency)
- Loan: `apr` (%), `termMonths`, `subtype` (mortgage, auto_loan, personal_loan, line_of_credit)
- IRA: `subtype` (traditional_ira, roth_ira, sep_ira)
- Rewards: `rewardsUnit` (e.g., "Points", "Miles")
- Checking/Savings/Brokerage: No extra fields

## Deviations from Plan

None - plan executed exactly as written.

## Integration Points

**Depends on:**
- 15-01: shadcn/ui Dialog, Select, RadioGroup, Separator, Badge components
- 15-01: react-currency-input-field library
- 15-01: API type definitions (AccountResponse, CreateAccountRequest types)

**Provides for:**
- 15-04: AccountWizard ready to wire with TanStack Query mutations
- 15-05: DeleteAccountDialog ready to wire with delete mutation
- Future plans: Reusable multi-step form pattern with progressive validation

## Next Phase Readiness

**Blockers:** None

**Outstanding questions:** None

**Tech debt:** None

**Ready for:** Plan 15-04 (Account CRUD Mutations and Query Hooks)

---

**Commits:**
- Task 1 (2964063): Zod validation schemas and ProgressDots component
- Task 2 (c523fd6): Wizard steps, container, and delete dialog

**Files:** 8 created (validation schema, 5 wizard components, container, delete dialog)

**Dependencies:** React Hook Form, Zod, @hookform/resolvers, shadcn/ui Dialog/Select/RadioGroup, lucide-react icons, react-currency-input-field

**Quality gates:** ✓ Typecheck passed
