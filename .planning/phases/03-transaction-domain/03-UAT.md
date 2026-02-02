---
status: complete
phase: 03-transaction-domain
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md]
started: 2026-02-02T04:35:00Z
updated: 2026-02-02T04:55:00Z
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

## Summary

total: 15
passed: 14
issues: 1
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
