# Quick Plan 002: Split Phase 4.3 into Event Publishing and Email Phases

## Overview

Phase 4.3 "Transactional Email Infrastructure" is too large - it combines two distinct concerns:
1. Domain event publishing/handling architecture (event bus pattern)
2. Email sending infrastructure (SMTP adapter, Mailpit, email delivery)

These should be split into separate phases for cleaner separation of concerns.

## Tasks

### Task 1: Rename Phase 4.3 to Phase 5 (Domain Event Publishing)

Update ROADMAP.md:
- Phase 4.3 becomes Phase 5: Domain Event Publishing
- Focus: Event bus infrastructure, async event handlers, event persistence
- Goal: Establish the domain event publishing pattern that other features can use

### Task 2: Create new Phase 6 (Transactional Email Infrastructure)

Update ROADMAP.md:
- Insert new Phase 6: Transactional Email Infrastructure
- Focus: Email domain, SMTP adapter, Mailpit dev env, verification emails
- Depends on Phase 5 (uses event system to trigger emails)
- Original Phase 4.3 success criteria move here

### Task 3: Renumber subsequent phases

Push all subsequent phases down by 1:
- Old Phase 5 (Nx Monorepo) → Phase 7
- Old Phase 6 (Frontend Infrastructure) → Phase 8
- Continue through Phase 20 → Phase 22
- Future milestone phases 21-26 → 23-28

### Task 4: Update STATE.md

Update references to:
- Next action after Phase 4.2
- Any mentions of Phase 4.3 or subsequent phases

## Acceptance Criteria

- [ ] Phase 5 is "Domain Event Publishing" (extracted from 4.3)
- [ ] Phase 6 is "Transactional Email Infrastructure" (remaining from 4.3)
- [ ] All phases 7-28 properly renumbered
- [ ] Progress table updated with new phase numbers
- [ ] STATE.md updated to reflect new structure
- [ ] No (INSERTED) tag on new phases 5 and 6 since they're now integer phases
