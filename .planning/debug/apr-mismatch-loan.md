---
status: diagnosed
trigger: "APR mismatch between frontend wizard (percentage) and backend API (decimal fraction) causes 422 on loan creation"
created: 2026-02-13T00:00:00Z
updated: 2026-02-13T00:01:00Z
---

## Current Focus

hypothesis: CONFIRMED - Frontend sends user-entered APR as-is (e.g. "6.5") without dividing by 100, but API validates apr <= 1 expecting decimal fraction (e.g. 0.065)
test: Traced full data flow from UI input through submission to API validation
expecting: No transformation anywhere
next_action: Return diagnosis

## Symptoms

expected: User enters 6.5% APR in wizard, loan account is created successfully
actual: 422 Unprocessable Entity - "Input should be less than or equal to 1"
errors: {"detail":[{"type":"less_than_equal","loc":["body","apr"],"msg":"Input should be less than or equal to 1","input":"6.5","ctx":{"le":1}}]}
reproduction: Create loan account via wizard, enter APR of 6.5
started: Since loan wizard was first implemented

## Eliminated

(none needed - hypothesis confirmed on first investigation)

## Evidence

- timestamp: 2026-02-13T00:00:30Z
  checked: StepDetails.tsx (UI input component)
  found: Label says "APR (%)" and placeholder is "3.5", clearly presenting to user as percentage. Input is registered as string via react-hook-form with {...register('apr')}.
  implication: User is prompted to enter a percentage value (e.g. 6.5 for 6.5%)

- timestamp: 2026-02-13T00:00:30Z
  checked: accountSchemas.ts (Zod validation)
  found: APR field is `z.string().optional()` with NO range validation and NO transformation. The raw string is passed through.
  implication: Frontend validation does not catch or convert the value

- timestamp: 2026-02-13T00:00:30Z
  checked: useCreateAccount.ts (mutation hook, loan case)
  found: Line 67 sends `apr: formData.apr || '0'` directly - no division by 100, no parseFloat, no transformation whatsoever
  implication: The raw user-entered string "6.5" is sent to the API as-is

- timestamp: 2026-02-13T00:00:30Z
  checked: StepReview.tsx (review step)
  found: Line 89 displays `{formData.apr}%` - appends "%" sign, confirming the UI treats the value as a percentage
  implication: UI consistently treats APR as percentage throughout

- timestamp: 2026-02-13T00:00:45Z
  checked: account.py Pydantic schema (API layer)
  found: Line 149 defines `apr: Annotated[Decimal, Field(ge=0, le=1)] | None` with description "Annual percentage rate as decimal (e.g., 0.0599 for 5.99%)"
  implication: API expects decimal fraction (0-1 range), rejects anything > 1

- timestamp: 2026-02-13T00:00:45Z
  checked: account.py domain model
  found: Line 60 documents `apr: Decimal | None = None  # e.g., 0.1999 for 19.99%`
  implication: Domain model also stores APR as decimal fraction

- timestamp: 2026-02-13T00:00:45Z
  checked: tables.py (database schema)
  found: Line 181 defines `Column("apr", Numeric(5, 4), nullable=True)  # e.g., 0.1999 for 19.99%`
  implication: Database column is Numeric(5,4) which can store 0.0000 to 9.9999 but semantically expects 0-1 range

- timestamp: 2026-02-13T00:00:50Z
  checked: api-types.generated.ts (OpenAPI generated types)
  found: Line 1155-1157 shows the description "Annual percentage rate as decimal (e.g., 0.0599 for 5.99%)" and type `number | string | null`
  implication: Generated types carry the backend's expectation but frontend ignores the description

## Resolution

root_cause: The frontend UI collects APR as a human-readable percentage (label says "APR (%)", placeholder "3.5") but sends it to the API without dividing by 100; the API schema validates apr <= 1 expecting a decimal fraction (0.065 for 6.5%).
fix:
verification:
files_changed: []
