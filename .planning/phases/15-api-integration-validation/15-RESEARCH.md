# Phase 15: API Integration Validation - Research

**Researched:** 2026-02-11
**Domain:** React frontend CRUD operations with TanStack Query, multi-step forms, shadcn/ui components
**Confidence:** HIGH

## Summary

Phase 15 builds account CRUD through the UI with a 4-step wizard modal, sidebar account list with grouping, and comprehensive integration testing. The standard approach uses React Hook Form + Zod for per-step validation, TanStack Query v5 mutations with optimistic updates, and shadcn/ui Dialog/RadioGroup/Select components. Transaction CRUD is explicitly deferred to Phase 17.

**Key findings:**
- Multi-step forms should validate per-step using separate Zod schemas, not a single monolithic schema
- TanStack Query v5 invalidateQueries in onSettled is safer than manual cache updates for CRUD operations
- shadcn/ui Dialog needs controlled state (open/onOpenChange) with explicit reset logic to prevent form state persistence across open/close cycles
- Progress indicators should use dots for 4-step wizards (not named steps or progress bars)
- Playwright E2E tests are critical for wizard flows - unit tests miss navigation/state reset bugs

**Primary recommendation:** Build the wizard modal design-first (visual task) before functionality task. Use React Hook Form with step-specific Zod schemas and controlled Dialog state with explicit useEffect reset on close. Invalidate queries in onSettled callbacks, don't manually update cache.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| TanStack Query | v5 | Server state management, mutations, caching | De facto standard for React async state - queryClient.invalidateQueries is safer than manual cache updates |
| React Hook Form | 7.x | Form state, validation integration | Most popular React form library - minimal re-renders, works with Zod |
| Zod | 3.x | Schema validation for forms | Type-safe validation schemas, best TypeScript integration with RHF |
| shadcn/ui | latest | UI components (Dialog, RadioGroup, Select) | CLI-addable Radix UI wrappers with Tailwind - already in libs/ui/ |
| MSW | v2 | API mocking for tests | Standard for mocking fetch/axios at network level - better than jest.mock |
| Playwright | latest | E2E testing for wizard flows | Cross-browser testing with auto-wait - catches UI bugs unit tests miss |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-currency-input-field | 3.x | Currency input formatting | Opening balance step - handles locale, decimal limits, value callbacks |
| @tanstack/react-query-devtools | v5 | Query debugging | Development only - visualize cache state during mutation testing |
| @hookform/resolvers | latest | Zod integration for RHF | Required for zodResolver(schema) pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TanStack Query | SWR | SWR simpler but TanStack Query already in project, better mutation support |
| React Hook Form | Formik | Formik more verbose, higher re-render count - RHF is lighter |
| Zod | Yup | Yup less strict TypeScript - Zod better type inference |
| Custom progress dots | MUI Stepper | MUI adds 300KB+ dependency for simple dot indicator |

**Installation:**
```bash
# Already installed in Phase 14:
# @tanstack/react-query, @tanstack/react-router, axios

# New dependencies needed:
pnpm add react-hook-form zod @hookform/resolvers react-currency-input-field

# shadcn/ui components (CLI install):
npx shadcn@latest add dialog select radio-group separator badge
```

## Architecture Patterns

### Recommended Project Structure
```
apps/web/src/
├── features/
│   └── accounts/
│       ├── components/
│       │   ├── AccountWizard.tsx          # Main wizard dialog container
│       │   ├── AccountWizardSteps/        # Step components
│       │   │   ├── StepTypeSelection.tsx  # Step 1: account type radio group
│       │   │   ├── StepDetails.tsx        # Step 2: name + type-specific fields
│       │   │   ├── StepOpeningBalance.tsx # Step 3: currency input
│       │   │   └── StepReview.tsx         # Step 4: confirmation view
│       │   ├── AccountSidebar.tsx         # Left sidebar with grouped accounts
│       │   ├── AccountList.tsx            # Account list with grouping
│       │   ├── AccountListItem.tsx        # Single account row (name + balance)
│       │   ├── DeleteAccountDialog.tsx    # Type-to-confirm delete modal
│       │   └── EmptyAccountsState.tsx     # Zero accounts welcome screen
│       ├── hooks/
│       │   ├── useAccounts.ts             # Query hook for fetchAccounts
│       │   ├── useCreateAccount.ts        # Mutation hook for create
│       │   ├── useUpdateAccount.ts        # Mutation hook for update
│       │   ├── useDeleteAccount.ts        # Mutation hook for delete
│       │   └── useAccountWizard.ts        # Multi-step form state manager
│       ├── validation/
│       │   └── accountSchemas.ts          # Zod schemas per wizard step
│       └── types.ts                       # Feature-specific types
└── lib/
    └── query-keys.ts                      # Query key factory (TkDodo pattern)
```

### Pattern 1: Multi-Step Form with React Hook Form

**What:** Each wizard step has its own Zod schema and validates independently. Form state persists across steps using React state.

**When to use:** 4-step wizard with different field sets per step (account type, details, balance, review).

**Example:**
```typescript
// Source: https://blog.logrocket.com/building-reusable-multi-step-form-react-hook-form-zod/
// apps/web/src/features/accounts/validation/accountSchemas.ts

import { z } from 'zod';

// Step 1: Account type selection
export const stepTypeSchema = z.object({
  accountType: z.enum(['checking', 'savings', 'credit_card', 'loan', 'brokerage', 'ira', 'rewards']),
});

// Step 2: Account details (conditional fields based on type)
export const stepDetailsSchema = z
  .object({
    name: z.string().min(1, 'Name is required').max(100),
    creditLimit: z.string().optional(), // For credit cards
    apr: z.string().optional(), // For loans
    subtype: z.enum(['traditional_ira', 'roth_ira', 'sep_ira']).optional(), // For IRAs
  })
  .refine((data) => {
    // Conditional validation based on accountType from previous step
    return true; // Add type-specific validation
  });

// Step 3: Opening balance
export const stepBalanceSchema = z.object({
  openingBalance: z.string().refine((val) => !isNaN(parseFloat(val)), {
    message: 'Invalid amount',
  }),
  openingDate: z.date(),
});

// Step 4: Review (no validation - read-only confirmation)
export const stepReviewSchema = z.object({});

// Hook for multi-step form state
export function useAccountWizard() {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({});

  const schemas = [stepTypeSchema, stepDetailsSchema, stepBalanceSchema, stepReviewSchema];
  const currentSchema = schemas[currentStep];

  const form = useForm({
    resolver: zodResolver(currentSchema),
    defaultValues: formData,
  });

  const goToNextStep = async () => {
    const isValid = await form.trigger(); // Validate current step
    if (isValid) {
      setFormData({ ...formData, ...form.getValues() });
      setCurrentStep((prev) => prev + 1);
    }
  };

  return { currentStep, form, goToNextStep, setCurrentStep, formData };
}
```

### Pattern 2: TanStack Query Mutations with Cache Invalidation

**What:** Use onMutate for optimistic updates, onError for rollback, onSettled for cache invalidation.

**When to use:** All CRUD mutations (create, update, delete account).

**Example:**
```typescript
// Source: https://tanstack.com/query/v5/docs/react/guides/optimistic-updates
// apps/web/src/features/accounts/hooks/useCreateAccount.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createCheckingAccount } from '@/lib/api-client';
import { accountKeys } from '@/lib/query-keys';

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCheckingAccount,
    onMutate: async (newAccount) => {
      // Cancel outgoing refetches (so they don't overwrite optimistic update)
      await queryClient.cancelQueries({ queryKey: accountKeys.lists() });

      // Snapshot previous value
      const previousAccounts = queryClient.getQueryData(accountKeys.lists());

      // Optimistically update to the new value
      queryClient.setQueryData(accountKeys.lists(), (old) => {
        return { accounts: [...(old?.accounts || []), newAccount] };
      });

      // Return context with snapshot
      return { previousAccounts };
    },
    onError: (err, newAccount, context) => {
      // Roll back to snapshot on error
      if (context?.previousAccounts) {
        queryClient.setQueryData(accountKeys.lists(), context.previousAccounts);
      }
    },
    onSettled: () => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}
```

### Pattern 3: Controlled Dialog with Form Reset

**What:** Dialog state controlled via open/onOpenChange props. Form resets when dialog closes to prevent stale data on reopen.

**When to use:** AccountWizard modal, DeleteAccountDialog - any dialog with form state.

**Example:**
```typescript
// Source: https://github.com/shadcn-ui/ui/discussions/1504
// apps/web/src/features/accounts/components/AccountWizard.tsx

import { Dialog, DialogContent, DialogHeader } from '@workspace/ui/components/dialog';
import { useAccountWizard } from '../hooks/useAccountWizard';

interface AccountWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editAccountId?: string; // For edit mode
}

export function AccountWizard({ open, onOpenChange, editAccountId }: AccountWizardProps) {
  const { currentStep, form, goToNextStep, setCurrentStep, formData } = useAccountWizard();

  // CRITICAL: Reset form when dialog closes
  useEffect(() => {
    if (!open) {
      setCurrentStep(0);
      form.reset();
    }
  }, [open, form, setCurrentStep]);

  const handleClose = () => {
    onOpenChange(false);
    // Reset happens in useEffect above
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <ProgressDots currentStep={currentStep} totalSteps={4} />
        </DialogHeader>
        {/* Render current step component */}
      </DialogContent>
    </Dialog>
  );
}
```

### Pattern 4: Query Key Factory (TkDodo v5 Pattern)

**What:** Hierarchical query keys for accounts: all -> lists() -> list(filters) -> detail(id).

**When to use:** All TanStack Query queries - enables targeted invalidation.

**Example:**
```typescript
// Source: https://tkdodo.eu/blog/effective-react-query-keys
// apps/web/src/lib/query-keys.ts

export const accountKeys = {
  all: ['accounts'] as const,
  lists: () => [...accountKeys.all, 'list'] as const,
  list: (filters: string) => [...accountKeys.lists(), { filters }] as const,
  details: () => [...accountKeys.all, 'detail'] as const,
  detail: (id: string) => [...accountKeys.details(), id] as const,
};

// Usage:
// queryClient.invalidateQueries({ queryKey: accountKeys.lists() }); // Invalidates all lists
// queryClient.invalidateQueries({ queryKey: accountKeys.detail(id) }); // Invalidates single account
```

### Pattern 5: Account Grouping by Type Category

**What:** Group accounts by category (Cash, Credit, Loans, Investments, Rewards) with subtotals.

**When to use:** Sidebar account list display.

**Example:**
```typescript
// apps/web/src/features/accounts/components/AccountList.tsx

const accountCategories = {
  cash: ['checking', 'savings'],
  credit: ['credit_card'],
  loans: ['loan'],
  investments: ['brokerage', 'ira'],
  rewards: ['rewards'],
};

function groupAccounts(accounts: AccountResponse[]) {
  return Object.entries(accountCategories).map(([category, types]) => {
    const categoryAccounts = accounts.filter((acc) => types.includes(acc.account_type));
    const subtotal = categoryAccounts.reduce((sum, acc) => sum + parseFloat(acc.balance), 0);
    return { category, accounts: categoryAccounts, subtotal };
  });
}
```

### Anti-Patterns to Avoid

- **Single monolithic Zod schema:** Don't validate all 4 steps with one schema - per-step schemas enable progressive validation
- **Uncontrolled Dialog:** Don't rely on Dialog to manage its own state - form state persists across close/reopen, causing stale data bugs
- **Manual cache updates without rollback:** Don't use setQueryData without onError rollback - optimistic updates need error handling
- **Excessive progress bar for 4 steps:** Don't use progress bar (0%-100%) for small step count - dots are clearer for 4 steps
- **No E2E tests for wizard:** Don't rely only on unit tests - wizard navigation bugs (back button, step reset) require E2E tests
- **Ignoring field count per step:** Don't put 10+ fields in one step - keep steps to 3-5 fields max (UX research: >5 fields feels overwhelming)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Currency input formatting | Custom input with regex | react-currency-input-field | Handles locale-specific formatting, decimal separators, thousands separators, prefix/suffix, accessibility |
| Progress dots indicator | Custom div with CSS | Simple custom component (no lib) | 4 dots is trivial - MUI Stepper adds 300KB for basic dots |
| Form validation | Manual validation functions | Zod + React Hook Form | Type-safe schemas, async validation, error messages, field-level validation |
| API state management | useState + useEffect | TanStack Query | Cache invalidation, optimistic updates, request deduplication, automatic refetching |
| Type-to-confirm delete | Custom input comparison | Simple controlled input with match check | Pattern is simple enough - existing packages (react-delete-confirm) add dependency for 10 lines of code |
| Account grouping logic | Ad-hoc array manipulation | Utility function with type safety | Grouping is straightforward but needs type guards for account_type |

**Key insight:** Multi-step forms have many edge cases (back navigation, validation state, step persistence) that look simple but aren't. React Hook Form + Zod solves 90% of the complexity. Currency formatting is deceptively hard (locale support, decimal handling, accessibility) - use react-currency-input-field.

## Common Pitfalls

### Pitfall 1: Dialog Form State Persists Across Close/Reopen

**What goes wrong:** User opens wizard, fills step 1, closes dialog, reopens - sees stale data from previous session instead of fresh form.

**Why it happens:** shadcn/ui Dialog (Radix UI) hides content on close, doesn't unmount. React Hook Form state persists in hidden DOM.

**How to avoid:**
- Use controlled Dialog state (open/onOpenChange props)
- Add useEffect that watches `open` prop and calls form.reset() when false
- Reset currentStep state to 0 when dialog closes

**Warning signs:**
- Wizard opens on step 2/3 instead of step 1
- Previously entered values appear in form fields
- Test: open wizard, type text, close, reopen - text still visible

**Reference:** [GitHub Issue #10663](https://github.com/orgs/react-hook-form/discussions/10663), [Radix Primitives Discussion #1518](https://github.com/radix-ui/primitives/discussions/1518)

### Pitfall 2: Invalidating Wrong Query Keys After Mutation

**What goes wrong:** After creating account, list doesn't update. After updating account, detail view shows stale data.

**Why it happens:** Query keys don't match between useQuery and invalidateQueries. TkDodo hierarchical pattern requires exact key structure.

**How to avoid:**
- Define query key factory in lib/query-keys.ts
- Use factory functions in both useQuery and invalidateQueries
- Use queryKey: accountKeys.lists() not ['accounts', 'list'] (array literal)
- Test invalidation: create account, check if list query refetches

**Warning signs:**
- Mutation succeeds but UI doesn't update
- Manual page refresh shows new data
- React Query DevTools shows stale queries not refetching

**Reference:** [TanStack Query Invalidation Guide](https://tanstack.com/query/v5/docs/react/guides/invalidations-from-mutations)

### Pitfall 3: Too Many Fields Per Wizard Step

**What goes wrong:** User abandons wizard because step 2 has 10+ fields and feels overwhelming.

**Why it happens:** Designer puts all account details in one step instead of progressive disclosure.

**How to avoid:**
- Limit steps to 3-5 fields maximum
- Use conditional fields (only show credit_limit if type is credit_card)
- Step 1: Single choice (account type)
- Step 2: Core details (name + 1-2 type-specific fields)
- Step 3: Single value (opening balance)
- Step 4: Read-only review

**Warning signs:**
- Step requires scrolling to see all fields
- Users click "back" after seeing step 2
- High wizard abandonment rate in analytics

**Reference:** [Growform Multi-Step UX Guide](https://www.growform.co/must-follow-ux-best-practices-when-designing-a-multi-step-form/) - "no more than 5 form fields per step"

### Pitfall 4: No Back Button in Wizard

**What goes wrong:** User makes typo in step 2, can't go back to fix it, has to cancel and restart wizard.

**Why it happens:** Developer assumes linear forward-only flow.

**How to avoid:**
- Add "Back" button to all steps except step 1
- Back button saves current step values before navigating
- Preserve validation state when going back
- Test: fill all steps, go back to step 2, edit value, forward again

**Warning signs:**
- Users cancel wizard and restart frequently
- Support requests about "can't edit previous step"
- High wizard abandonment on later steps

**Reference:** [Multi-Step Form Best Practices](https://www.formassembly.com/blog/multi-step-form-best-practices/) - "removing the back button creates anxiety and abandonment"

### Pitfall 5: Missing Progress Indicator

**What goes wrong:** User doesn't know how many steps remain, abandons wizard thinking it's too long.

**Why it happens:** No visual indicator of "Step 2 of 4" or progress dots.

**How to avoid:**
- Add progress dots at top of dialog (4 dots for 4 steps)
- Highlight current step dot
- Don't use text labels (clutters header) - dots are sufficient for 4 steps
- Test: users should know completion progress at a glance

**Warning signs:**
- Users ask "how many more steps?"
- Analytics show drop-off after step 2 (users assume more steps coming)
- UX testing reveals anxiety about wizard length

**Reference:** [Multi-Step Form UX Research](https://www.growform.co/must-follow-ux-best-practices-when-designing-a-multi-step-form/) - "24% abandon due to lack of clarity on completion status"

### Pitfall 6: Account Type Not Locked During Edit

**What goes wrong:** User edits checking account, changes type to credit card, breaks data model (missing credit_limit).

**Why it happens:** Edit form allows changing account_type without clearing type-specific fields.

**How to avoid:**
- Lock account_type field during edit (display as read-only text, not select)
- CONTEXT.md decision: "Account type is locked after creation"
- If future enhancement allows type change, must clear incompatible fields
- Test: edit account, verify type field is disabled

**Warning signs:**
- 500 errors from API due to missing required fields for new type
- Data integrity issues (credit card without credit_limit)
- Support tickets about "can't change account type"

## Code Examples

Verified patterns from official sources:

### Multi-Step Form State Management

```typescript
// Source: https://blog.logrocket.com/building-reusable-multi-step-form-react-hook-form-zod/
// apps/web/src/features/accounts/hooks/useAccountWizard.ts

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const stepSchemas = [
  stepTypeSchema,
  stepDetailsSchema,
  stepBalanceSchema,
  stepReviewSchema,
];

export function useAccountWizard(editAccountId?: string) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Partial<AccountFormData>>({});

  const form = useForm({
    resolver: zodResolver(stepSchemas[currentStep]),
    defaultValues: formData,
    mode: 'onChange', // Validate on change for immediate feedback
  });

  const goToNextStep = async () => {
    const isValid = await form.trigger();
    if (isValid) {
      setFormData({ ...formData, ...form.getValues() });
      setCurrentStep((prev) => Math.min(prev + 1, stepSchemas.length - 1));
      form.clearErrors(); // Clear errors from previous step
    }
  };

  const goToPreviousStep = () => {
    setFormData({ ...formData, ...form.getValues() }); // Save current values
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const reset = () => {
    setCurrentStep(0);
    setFormData({});
    form.reset();
  };

  return {
    currentStep,
    totalSteps: stepSchemas.length,
    form,
    formData,
    goToNextStep,
    goToPreviousStep,
    reset,
    isFirstStep: currentStep === 0,
    isLastStep: currentStep === stepSchemas.length - 1,
  };
}
```

### TanStack Query Mutation with Optimistic Update

```typescript
// Source: https://tanstack.com/query/v5/docs/react/guides/optimistic-updates
// apps/web/src/features/accounts/hooks/useUpdateAccount.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateAccount } from '@/lib/api-client';
import { accountKeys } from '@/lib/query-keys';
import type { UpdateAccountRequest, AccountResponse } from '@/lib/api-client';

export function useUpdateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAccountRequest }) =>
      updateAccount(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: accountKeys.detail(id) });
      await queryClient.cancelQueries({ queryKey: accountKeys.lists() });

      const previousAccount = queryClient.getQueryData<AccountResponse>(
        accountKeys.detail(id)
      );
      const previousList = queryClient.getQueryData(accountKeys.lists());

      // Optimistic update for detail view
      queryClient.setQueryData(accountKeys.detail(id), (old: AccountResponse) => ({
        ...old,
        ...data,
      }));

      // Optimistic update for list view
      queryClient.setQueryData(accountKeys.lists(), (old: any) => ({
        accounts: old?.accounts?.map((acc: AccountResponse) =>
          acc.id === id ? { ...acc, ...data } : acc
        ),
      }));

      return { previousAccount, previousList };
    },
    onError: (err, { id }, context) => {
      if (context?.previousAccount) {
        queryClient.setQueryData(accountKeys.detail(id), context.previousAccount);
      }
      if (context?.previousList) {
        queryClient.setQueryData(accountKeys.lists(), context.previousList);
      }
    },
    onSettled: (data, error, { id }) => {
      queryClient.invalidateQueries({ queryKey: accountKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}
```

### Type-to-Confirm Delete Dialog

```typescript
// Source: https://codemoto.io/coding/react/react-delete-confirmation-modal
// apps/web/src/features/accounts/components/DeleteAccountDialog.tsx

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@workspace/ui/components/dialog';
import { Input } from '@workspace/ui/components/input';
import { Button } from '@workspace/ui/components/button';

interface DeleteAccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountName: string;
  accountId: string;
  onConfirmDelete: (id: string) => void;
}

export function DeleteAccountDialog({
  open,
  onOpenChange,
  accountName,
  accountId,
  onConfirmDelete,
}: DeleteAccountDialogProps) {
  const [confirmText, setConfirmText] = useState('');

  const handleClose = () => {
    setConfirmText('');
    onOpenChange(false);
  };

  const handleDelete = () => {
    if (confirmText === accountName) {
      onConfirmDelete(accountId);
      handleClose();
    }
  };

  const isConfirmed = confirmText === accountName;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Account</DialogTitle>
          <DialogDescription>
            This action cannot be undone. Type <strong>{accountName}</strong> to confirm deletion.
          </DialogDescription>
        </DialogHeader>
        <Input
          value={confirmText}
          onChange={(e) => setConfirmText(e.target.value)}
          placeholder={`Type "${accountName}" to confirm`}
        />
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={!isConfirmed}>
            Delete Account
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Progress Dots Component

```typescript
// Simple custom component - no library needed for 4 dots
// apps/web/src/features/accounts/components/ProgressDots.tsx

interface ProgressDotsProps {
  currentStep: number;
  totalSteps: number;
}

export function ProgressDots({ currentStep, totalSteps }: ProgressDotsProps) {
  return (
    <div className="flex items-center justify-center gap-2" role="progressbar" aria-valuenow={currentStep + 1} aria-valuemin={1} aria-valuemax={totalSteps}>
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div
          key={index}
          className={`h-2 w-2 rounded-full transition-colors ${
            index === currentStep
              ? 'bg-primary'
              : index < currentStep
              ? 'bg-primary/50'
              : 'bg-muted'
          }`}
          aria-label={`Step ${index + 1}${index === currentStep ? ' (current)' : index < currentStep ? ' (completed)' : ''}`}
        />
      ))}
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Formik + Yup | React Hook Form + Zod | 2021-2022 | Better TypeScript inference, fewer re-renders |
| Redux for form state | React Hook Form local state | 2020-2021 | Simpler architecture, no global store pollution |
| Manual fetch + useState | TanStack Query | 2020+ | Built-in caching, optimistic updates, request deduplication |
| Custom mutation logic | useMutation with onMutate/onError/onSettled | TanStack Query v4-v5 | Standardized optimistic update pattern |
| Uncontrolled forms | Controlled forms with validation | 2019+ | Better UX with real-time validation feedback |
| MUI Stepper for progress | Simple CSS dots | 2023+ | Avoid heavy UI library for basic indicator |
| Manual cache updates | queryClient.invalidateQueries | TanStack Query best practices | Safer than setQueryData - avoids stale data |

**Deprecated/outdated:**
- Formik: Still works but React Hook Form is lighter and has better TypeScript
- Redux for forms: Overkill for local form state - use React Hook Form
- Class components for forms: Hooks-based forms are standard now
- Uncontrolled inputs for multi-step: Need controlled state to preserve values across steps

## Open Questions

Things that couldn't be fully resolved:

1. **Currency input for multi-currency support**
   - What we know: react-currency-input-field supports locale config (e.g., ₹5,00,000 for INR)
   - What's unclear: Backend currently hardcoded to USD - does frontend need currency selector now or wait for Phase 18 (multi-currency)?
   - Recommendation: Hardcode USD in opening balance step for Phase 15, add currency selector in Phase 18 when backend supports it

2. **Account sidebar collapse/expand behavior**
   - What we know: CONTEXT.md says "Claude's discretion" for collapse behavior
   - What's unclear: Should sidebar remember collapsed state in localStorage? Should groups be individually collapsible?
   - Recommendation: Make groups (Cash, Credit, etc.) individually collapsible with state in localStorage. Don't add full sidebar collapse (narrow screen = hide sidebar entirely via responsive design)

3. **Empty state illustration choice**
   - What we know: CONTEXT.md says "Claude's discretion" for illustration
   - What's unclear: Use icon, SVG illustration, or placeholder image?
   - Recommendation: Use simple icon (Lucide icon: Wallet or CircleDollarSign) with centered text. Avoid custom illustrations (require design assets). Defer fancy illustrations to future design iteration.

4. **Loading states during wizard submission**
   - What we know: WEB-06 requires loading states during API calls
   - What's unclear: Should wizard disable all steps during submission or just show spinner on submit button?
   - Recommendation: Disable "Create Account" button on step 4 with loading spinner. Don't disable navigation between steps (user might want to go back and cancel). Show toast on success/error.

5. **Playwright vs Chrome DevTools for E2E testing**
   - What we know: Project uses Playwright with Chromium, also has Chrome DevTools MCP from Phase 13
   - What's unclear: Which to use for wizard E2E tests?
   - Recommendation: Use Playwright for automated regression tests (configured in Phase 14). Use Chrome DevTools MCP for manual UAT smoke testing during development. Playwright is better for CI/CD.

## Sources

### Primary (HIGH confidence)
- [TanStack Query v5 Optimistic Updates](https://tanstack.com/query/v5/docs/react/guides/optimistic-updates) - Official mutation patterns
- [TanStack Query v5 Invalidations](https://tanstack.com/query/v5/docs/react/guides/invalidations-from-mutations) - Cache invalidation strategies
- [shadcn/ui Components](https://ui.shadcn.com/docs/components) - Dialog, RadioGroup, Select documentation
- [React Hook Form Advanced Usage](https://react-hook-form.com/advanced-usage) - Multi-step form patterns
- TkDodo Query Keys Pattern - Hierarchical query key factory (verified in existing codebase: apps/web/src/lib/query-keys.ts would follow this if created)

### Secondary (MEDIUM confidence)
- [Building Reusable Multi-Step Form with React Hook Form and Zod - LogRocket](https://blog.logrocket.com/building-reusable-multi-step-form-react-hook-form-zod/) - Step-by-step validation pattern
- [Multi-Step Form UX Best Practices - Growform](https://www.growform.co/must-follow-ux-best-practices-when-designing-a-multi-step-form/) - Field count limits, progress indicators
- [Globally Manage Toast Notifications with TanStack Query - Atomic Object](https://spin.atomicobject.com/toast-notifications-tanstack-query/) - MutationCache error handling
- [react-currency-input-field npm](https://www.npmjs.com/package/react-currency-input-field) - Currency input library
- [React Delete Confirmation Modal - Codemoto](https://codemoto.io/coding/react/react-delete-confirmation-modal) - Type-to-confirm pattern

### Tertiary (LOW confidence)
- [Guide to Playwright E2E Testing - DeviQA](https://www.deviqa.com/blog/guide-to-playwright-end-to-end-testing-in-2025/) - General E2E patterns
- [Testing React with MSW and Vitest - Frontend Weekly](https://medium.com/front-end-weekly/testing-react-applications-the-easy-way-with-testing-library-msw-and-vitest-using-a-sample-932916433203) - MSW setup patterns
- [MUI Stepper Component](https://mui.com/material-ui/react-stepper/) - Alternative to custom progress dots (not recommended due to bundle size)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - TanStack Query v5, React Hook Form, Zod, shadcn/ui all verified in official docs and existing codebase
- Architecture: HIGH - Multi-step form pattern verified in LogRocket tutorial and React Hook Form docs, query key factory from TkDodo is industry standard
- Pitfalls: HIGH - Dialog state persistence, query invalidation, field count limits all sourced from official GitHub issues and UX research
- Code examples: HIGH - All examples based on official TanStack Query docs, React Hook Form docs, or verified community tutorials

**Research date:** 2026-02-11
**Valid until:** 2026-03-13 (30 days - stable ecosystem, React Hook Form and TanStack Query APIs are mature)
