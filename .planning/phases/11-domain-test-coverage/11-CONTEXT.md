# Phase 11: Domain Test Coverage - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Add domain unit tests for Transaction, Category, and Payee models that currently have zero domain-level test coverage. Increase domain coverage from 48% toward 70%+. No new features or model changes — purely additive test coverage.

</domain>

<decisions>
## Implementation Decisions

### Coverage approach
- Fill gaps where coverage is zero or very low — Transaction, Category, Payee models
- Follow existing test patterns already established in the domain test suite (test_account.py, test_user.py, etc.)
- Example-based tests matching the style of existing domain tests (not property-based unless model arithmetic warrants it)

### Models to cover (priority order)
- Transaction aggregate (largest, most complex — factory methods, mutations, status progression, mirror creation, split validation, events)
- Category entity (hierarchy, system category protection, mutations, events)
- Payee entity (simplest — creation, normalization, usage tracking)

### Claude's Discretion
- Test class structure and grouping within each test file
- Which edge cases to prioritize beyond the obvious invariants
- Whether to use Hypothesis for any specific behaviors (e.g., split sum validation)
- Test naming conventions (follow existing patterns)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — follow existing test patterns in the domain test suite and cover the key invariants documented in each model.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-domain-test-coverage*
*Context gathered: 2026-02-09*
