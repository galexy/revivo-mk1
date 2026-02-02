---
phase: 03-transaction-domain
plan: 05
subsystem: application-services
tags: [transaction, category, service, crud, mirror-transactions]
completed: 2026-02-02

requires:
  - "03-04: Transaction repository for persistence"
  - "03-02: Transaction aggregate for domain logic"
  - "02-05: Account repository for validation"
provides:
  - "CategoryService with CRUD and hierarchy support"
  - "TransactionService with full CRUD, split updates, mirror sync"
  - "Auto-payee creation pattern"
affects:
  - "03-06: REST API endpoints will use these services"

tech-stack:
  added: []
  patterns:
    - "Application service pattern with UnitOfWork"
    - "Error dataclass for explicit failure handling"
    - "Mirror transaction synchronization"

key-files:
  created:
    - src/application/services/category_service.py
    - src/application/services/transaction_service.py
  modified:
    - src/domain/model/transaction.py

decisions:
  - "CategoryError/TransactionError dataclasses for explicit failures (matches AccountError pattern)"
  - "Mirror sync handled in service layer via _sync_mirrors_for_split_update"
  - "update_amount method added to Transaction for mirror amount sync"

metrics:
  duration: "2 min"
  files_created: 2
  files_modified: 1
  lines_added: ~875
---

# Phase 3 Plan 5: Transaction Application Service Summary

Application services for Transaction and Category domains with full CRUD, split updates, and mirror transaction synchronization.

## One-Liner

CategoryService and TransactionService with auto-payee creation, mirror transaction sync, and UnitOfWork transaction boundaries.

## What Was Built

### CategoryService (src/application/services/category_service.py)

Application service for category management:

- `ensure_system_categories(user_id)` - Creates Uncategorized if needed
- `create_category(user_id, name, parent_id, icon)` - With parent validation
- `get_category(category_id)` - Retrieve by ID
- `get_user_categories(user_id)` - All categories for user
- `get_category_tree(user_id)` - Hierarchical tree structure
- `update_category_name(user_id, category_id, new_name)` - With ownership check
- `update_category_parent(user_id, category_id, new_parent_id)` - Move in hierarchy
- `delete_category(user_id, category_id, reassign_to)` - With child/transaction checks

Key validations:
- Parent must exist and belong to user
- Cannot nest under system categories
- Cannot delete system categories
- Cannot delete categories with children or transactions

### TransactionService (src/application/services/transaction_service.py)

Application service for transaction management:

**Create:**
- `create_transaction(...)` - With auto-payee creation and mirror creation

**Read:**
- `get_transaction(user_id, transaction_id)` - Single transaction
- `get_account_transactions(user_id, account_id, limit, offset)` - By account
- `search_transactions(user_id, query, limit)` - Full-text search
- `filter_transactions(...)` - Multi-criteria filtering

**Update:**
- `update_transaction_memo(user_id, transaction_id, memo)` - Syncs to mirrors
- `update_transaction_dates(user_id, transaction_id, effective_date, posted_date)` - Effective syncs to mirrors
- `update_transaction_splits(user_id, transaction_id, new_splits, new_amount)` - Full mirror sync

**Status:**
- `mark_transaction_cleared(user_id, transaction_id, posted_date)` - PENDING -> CLEARED
- `mark_transaction_reconciled(user_id, transaction_id)` - -> RECONCILED

**Delete:**
- `delete_transaction(user_id, transaction_id)` - Cascades to mirrors

### Mirror Transaction Synchronization

Per CONTEXT decisions, mirror transactions are synced:
- **Created** when transfer splits added
- **Updated** when transfer split amounts change
- **Deleted** when transfer splits removed
- **Effective date** syncs from source to mirrors
- **Posted date** remains independent
- **Memo** syncs from source to mirrors
- Cannot update/delete mirror directly (must modify source)

### Transaction.update_amount Method

Added to Transaction aggregate for mirror sync:
- Updates amount and single split for mirror transactions
- Used by TransactionService when source splits change

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added update_amount method to Transaction**
- **Found during:** Task 2
- **Issue:** TransactionService._sync_mirrors_for_split_update needs to update mirror amounts, but Transaction lacked this method
- **Fix:** Added update_amount() method that updates amount and syncs single split for mirrors
- **Files modified:** src/domain/model/transaction.py
- **Commit:** 98afef5

## Verification

```bash
# Services import
python -c "
from src.application.services.category_service import CategoryService
from src.application.services.transaction_service import TransactionService
print('OK')
"

# lint-imports passes
lint-imports
# Contracts: 2 kept, 0 broken
```

## Commits

| Hash | Description |
|------|-------------|
| b58fc64 | feat(03-05): create CategoryService application service |
| 98afef5 | feat(03-05): create TransactionService application service |

## Next Phase Readiness

**Ready for Plan 06: Transaction REST API**

Services provide all necessary operations:
- Full CRUD for transactions and categories
- Validation and error handling via Error dataclasses
- Mirror transaction management is transparent to API layer

**Dependencies satisfied:**
- CategoryService.ensure_system_categories for user onboarding
- TransactionService.create_transaction with auto-payee
- TransactionService.update_transaction_splits with mirror sync
