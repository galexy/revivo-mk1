---
status: complete
phase: 03-transaction-domain
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md]
started: 2026-02-02T04:35:00Z
updated: 2026-02-02T13:00:00Z
---

## Setup

Start the API server:
```bash
uvicorn src.adapters.api.app:create_app --factory --reload
```

## Current Test

[testing complete]

## Tests

### 1. Create a Category
expected: Returns 201 with category object containing id (starts with cat_), name="Groceries", is_system=false.
command: |
  curl -X POST http://localhost:8000/api/v1/categories \
    -H "Content-Type: application/json" \
    -d '{"name": "Groceries"}'
result: pass

### 2. Create Subcategory
expected: Returns 201 with parent_id matching the category created in test 1.
command: |
  curl -X POST http://localhost:8000/api/v1/categories \
    -H "Content-Type: application/json" \
    -d '{"name": "Restaurants", "parent_id": "<CATEGORY_ID_FROM_TEST_1>"}'
result: pass

### 3. View Category Tree
expected: Returns hierarchical structure with "root" array and "children" map. Groceries appears in root, Restaurants in children.
command: |
  curl http://localhost:8000/api/v1/categories/tree
result: pass

### 4. Create Account (Setup for Transactions)
expected: Returns 201 with account id starting with acct_.
command: |
  curl -X POST http://localhost:8000/api/v1/accounts/checking \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Checking", "opening_balance": {"amount": "1000.00", "currency": "USD"}}'
result: pass

### 5. Create Simple Transaction
expected: Returns 201 with transaction containing id (txn_), status=pending, is_mirror=false, payee_name, and one split.
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<ACCOUNT_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-50.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-50.00", "currency": "USD"}, "category_id": "<CATEGORY_ID>"}],
      "payee_name": "Whole Foods",
      "memo": "Weekly groceries"
    }'
result: pass

### 6. Create Split Transaction
expected: Returns 201 with two splits totaling -100.00. Each split has its category_id.
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<ACCOUNT_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-100.00", "currency": "USD"},
      "splits": [
        {"amount": {"amount": "-60.00", "currency": "USD"}, "category_id": "<CATEGORY_ID>", "memo": "Food"},
        {"amount": {"amount": "-40.00", "currency": "USD"}, "category_id": "<CATEGORY_ID>", "memo": "Household"}
      ],
      "payee_name": "Target"
    }'
result: issue
reported: "passes if I give it proper ids. But, if I don't, I get an internal server error."
severity: minor

### 7. Create Second Account (for Transfer)
expected: Returns 201 with savings account id.
command: |
  curl -X POST http://localhost:8000/api/v1/accounts/savings \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Savings", "opening_balance": {"amount": "0.00", "currency": "USD"}}'
result: pass

### 8. Create Transfer (Mirror Creation)
expected: Returns 201 with source transaction (is_mirror=false, negative amount). Then query savings shows mirror (is_mirror=true, positive amount).
command: |
  # Create transfer from checking to savings
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-500.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-500.00", "currency": "USD"}, "transfer_account_id": "<SAVINGS_ID>"}],
      "memo": "Monthly savings"
    }'

  # Verify mirror exists in savings
  curl "http://localhost:8000/api/v1/transactions?account_id=<SAVINGS_ID>"
result: pass

### 9. Split Validation (Mismatch)
expected: Returns 400 with error code INVALID_SPLITS when splits don't sum to amount.
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<ACCOUNT_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-100.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-50.00", "currency": "USD"}, "category_id": "<CATEGORY_ID>"}]
    }'
result: pass

### 10. Search Transactions
expected: Returns transactions matching the search term in payee or memo.
command: |
  curl "http://localhost:8000/api/v1/transactions?search=Whole%20Foods"
result: pass

### 11. Filter by Date Range
expected: Returns only transactions within the specified date range.
command: |
  curl "http://localhost:8000/api/v1/transactions?date_from=2026-02-01&date_to=2026-02-28"
result: pass

### 12. Mark Transaction Cleared
expected: Returns 200 with status changed to "cleared".
command: |
  curl -X POST http://localhost:8000/api/v1/transactions/<TRANSACTION_ID>/clear
result: pass

### 13. Delete Transaction
expected: Returns 204. Subsequent GET returns 404.
command: |
  # Delete
  curl -X DELETE http://localhost:8000/api/v1/transactions/<TRANSACTION_ID>

  # Verify gone
  curl http://localhost:8000/api/v1/transactions/<TRANSACTION_ID>
result: pass

### 14. Delete Source Deletes Mirrors
expected: After deleting the source transfer transaction, the mirror in savings account is also gone.
command: |
  # Delete source transaction
  curl -X DELETE http://localhost:8000/api/v1/transactions/<SOURCE_TXN_ID>

  # Verify mirror gone
  curl http://localhost:8000/api/v1/transactions/<MIRROR_TXN_ID>
result: pass

### 15. Cannot Delete Mirror Directly
expected: Returns 400 with error code CANNOT_DELETE_MIRROR.
command: |
  curl -X DELETE http://localhost:8000/api/v1/transactions/<MIRROR_TXN_ID>
result: pass

### 16. Mixed Splits: Category + Transfer
expected: Returns 201 with transaction containing both a category split AND a transfer split. Mirror created for transfer portion only.
command: |
  # Pay $500 credit card bill from checking, get $20 cash back to wallet
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-480.00", "currency": "USD"},
      "splits": [
        {"amount": {"amount": "-500.00", "currency": "USD"}, "transfer_account_id": "<CREDIT_CARD_ID>"},
        {"amount": {"amount": "20.00", "currency": "USD"}, "category_id": "<CASH_BACK_CATEGORY_ID>", "memo": "Cash back reward"}
      ],
      "payee_name": "Credit Card Payment"
    }'
result: pass

### 17. Transfer to Self (Same Account)
expected: Returns 400 with error - cannot transfer to same account.
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-100.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-100.00", "currency": "USD"}, "transfer_account_id": "<CHECKING_ID>"}]
    }'
result: pass

### 18. Positive Transfer Split (Invalid)
expected: Returns 400 - transfer splits must be negative (outgoing from source).
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "100.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "100.00", "currency": "USD"}, "transfer_account_id": "<SAVINGS_ID>"}]
    }'
result: pass

### 19. Income Transaction (Positive Amount)
expected: Returns 201 with positive amount and positive split (e.g., paycheck deposit).
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "2500.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "2500.00", "currency": "USD"}, "category_id": "<INCOME_CATEGORY_ID>"}],
      "payee_name": "Employer Inc",
      "memo": "Paycheck"
    }'
result: pass

### 20. Mixed Income/Expense Splits
expected: Returns 201 - a refund scenario where you get money back but also pay a restocking fee.
command: |
  # Return item: $100 refund minus $15 restocking fee = $85 net income
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "85.00", "currency": "USD"},
      "splits": [
        {"amount": {"amount": "100.00", "currency": "USD"}, "category_id": "<REFUND_CATEGORY_ID>", "memo": "Item refund"},
        {"amount": {"amount": "-15.00", "currency": "USD"}, "category_id": "<FEE_CATEGORY_ID>", "memo": "Restocking fee"}
      ],
      "payee_name": "Best Buy"
    }'
result: pass

### 21. Empty Splits Array
expected: Returns 400 - transaction must have at least one split.
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-50.00", "currency": "USD"},
      "splits": []
    }'
result: pass
note: "Returns 422 (Unprocessable Entity) - semantically correct for validation"

### 22. Cannot Reconcile Pending Transaction
expected: Returns 400 - must be cleared before reconciling.
command: |
  # Create a new pending transaction
  TXN=$(curl -s -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-25.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-25.00", "currency": "USD"}, "category_id": "<CATEGORY_ID>"}]
    }' | jq -r '.id')

  # Try to reconcile without clearing first
  curl -X POST "http://localhost:8000/api/v1/transactions/${TXN}/reconcile"
result: pass

### 23. Cannot Modify Mirror Directly (PATCH)
expected: Returns 400 - mirrors can only be modified through source transaction.
command: |
  curl -X PATCH http://localhost:8000/api/v1/transactions/<MIRROR_TXN_ID> \
    -H "Content-Type: application/json" \
    -d '{"memo": "Trying to modify mirror"}'
result: pass

### 24. Update Transfer Amount Syncs Mirror
expected: After updating source transaction's transfer split amount, mirror's amount should also change.
command: |
  # Update source transaction to change transfer amount from -500 to -600
  curl -X PATCH http://localhost:8000/api/v1/transactions/<SOURCE_TXN_ID> \
    -H "Content-Type: application/json" \
    -d '{
      "amount": {"amount": "-600.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-600.00", "currency": "USD"}, "transfer_account_id": "<SAVINGS_ID>"}]
    }'

  # Verify mirror now shows +600
  curl http://localhost:8000/api/v1/transactions/<MIRROR_TXN_ID>
result: pass

### 25. Delete Category With Transactions
expected: Returns 400 - cannot delete category that has transactions assigned.
command: |
  # Try to delete a category that was used in test 5
  curl -X DELETE http://localhost:8000/api/v1/categories/<USED_CATEGORY_ID>
result: pass

### 26. Transaction With Subcategory
expected: Returns 201 - can assign transaction to a subcategory (child of parent).
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-45.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-45.00", "currency": "USD"}, "category_id": "<SUBCATEGORY_ID>"}],
      "payee_name": "Chipotle"
    }'
result: pass

### 27. Split With Both Category AND Transfer (Invalid)
expected: Returns 400 - a single split cannot have both category_id and transfer_account_id.
command: |
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-100.00", "currency": "USD"},
      "splits": [{"amount": {"amount": "-100.00", "currency": "USD"}, "category_id": "<CATEGORY_ID>", "transfer_account_id": "<SAVINGS_ID>"}]
    }'
result: pass

### 28. Multiple Transfers in One Transaction
expected: Returns 201 - can split payment across multiple destination accounts.
command: |
  # Split $1000 between savings and investment accounts
  curl -X POST http://localhost:8000/api/v1/transactions \
    -H "Content-Type: application/json" \
    -d '{
      "account_id": "<CHECKING_ID>",
      "effective_date": "2026-02-02",
      "amount": {"amount": "-1000.00", "currency": "USD"},
      "splits": [
        {"amount": {"amount": "-600.00", "currency": "USD"}, "transfer_account_id": "<SAVINGS_ID>"},
        {"amount": {"amount": "-400.00", "currency": "USD"}, "transfer_account_id": "<INVESTMENT_ID>"}
      ],
      "memo": "Monthly savings allocation"
    }'

  # Verify mirrors created in both accounts
  curl "http://localhost:8000/api/v1/transactions?account_id=<SAVINGS_ID>"
  curl "http://localhost:8000/api/v1/transactions?account_id=<INVESTMENT_ID>"
result: pass

## Summary

total: 28
passed: 27
issues: 4
pending: 0
skipped: 0

## Gaps

- truth: "Invalid account_id or category_id should return 400/404 with descriptive error"
  status: failed
  reason: "User reported: passes if I give it proper ids. But, if I don't, I get an internal server error."
  severity: minor
  test: 6
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Split must have either category_id or transfer_account_id, not neither"
  status: failed
  reason: "User reported: empty string for category creates a split with null for both transfer_account_id and category_id"
  severity: minor
  test: 16
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Categories should have income/expense type to indicate default transaction direction"
  status: enhancement
  reason: "User reported: categories don't have a type associated with them. Should add income and expense type to categories to tell what their default direction is (based on account type)"
  severity: minor
  test: 19
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Mirror update behavior with multiple splits to same account should be well-defined"
  status: investigation
  reason: "User reported: unclear if changing transfer account updates existing mirror or creates new one. Also unclear how updates work with multiple split lines transferring to the same account."
  severity: minor
  test: 24
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
