# Phase 10: Value Object ORM Mapping - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace manual value object decomposition/reconstruction with SQLAlchemy composite() mappings for Money, InstitutionDetails, and RewardsBalance on the Account aggregate. No database schema changes. No changes to Transaction/SplitLine mapping. EntityId/enum reconstruction stays as-is (separate concern).

</domain>

<decisions>
## Implementation Decisions

### Nullable composite handling
- When all underlying columns are NULL, the domain attribute should be `None` (e.g., `credit_limit=None`)
- Partial NULL for InstitutionDetails: if `name` is present, reconstruct as InstitutionDetails with None optional fields. Only return `None` when ALL columns are NULL
- Same composite type for both required Money (opening_balance) and nullable Money (credit_limit) — nullable handled by SQLAlchemy composite configuration or custom create_fn
- Partial NULL for 2-column composites (Money, RewardsBalance) is a data integrity issue — let it error, don't handle gracefully
- Composite mapping must handle both read AND write automatically — no before_flush handler for NULL writes
- Claude decides the best mechanism for null handling (create_fn vs __composite_values__ sentinel)

### Reconstruction scope
- Phase 10 scope is strictly value object composites: Money, InstitutionDetails, RewardsBalance
- EntityId and enum reconstruction in AccountRepository stays untouched (separate concern)
- After removing value object logic, rename `_reconstruct_value_objects` to `_reconstruct_identifiers`
- TransactionRepository not touched — Account aggregate only
- Remaining type: ignore comments for non-composite code (EntityId/enum) are acceptable

### __composite_values__() placement
- Add `__composite_values__()` directly to domain value objects (Money, InstitutionDetails, RewardsBalance)
- Method has zero imports — just returns a tuple of plain values (e.g., `return (self.amount, self.currency)`)
- Add incrementally: add `__composite_values__()` to each value object when its composite() mapping is implemented
- Verify during planning that import-linter is not triggered by `__composite_values__()` method names

### Migration strategy
- Single plan with incremental tasks (not multiple plans)
- First task: verify SQLAlchemy version supports composite() with frozen dataclasses and nullable handling
- Full verification ladder required: typecheck -> test -> serve -> smoke test
- Rollback strategy: git revert (no schema changes, safe to revert)

### Claude's Discretion
- Exact create_fn vs __composite_values__ approach for null handling
- Task granularity within the single plan
- Whether to tackle both Money composites in one task or separately
- Exact pyright strict annotations for composite() return types

</decisions>

<specifics>
## Specific Ideas

- The _decompose_value_objects handler has 20+ type: ignore[attr-defined] comments that should all be eliminated
- Current _reconstruct_value_objects is ~100 lines; value object portion should collapse into zero explicit code (handled by composite)
- All four value objects already accept positional constructor args, which is what composite() needs

</specifics>

<deferred>
## Deferred Ideas

- EntityId/enum TypeDecorator cleanup (verify if manual reconstruction is actually redundant) — future cleanup phase
- Transaction.amount composite() mapping — future phase if warranted
- SplitLine Money reconstruction — uses SQLAlchemy Core, not ORM mapping, different pattern

</deferred>

---

*Phase: 10-value-object-orm-mapping*
*Context gathered: 2026-02-09*
