---
status: complete
phase: 06-transactional-email-infrastructure
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md, 06-05-SUMMARY.md]
started: 2026-02-07T12:00:00Z
updated: 2026-02-07T04:50:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 8
name: Async chain is correct
expected: |
  All key functions in the async publish chain are coroutine functions
awaiting: completed - pass

## Setup

Start the app with job queue enabled (needs postgres-jobs), clear Mailpit inbox:
```bash
# Delete all Mailpit messages for clean slate
curl -s -X DELETE http://mailpit:8025/api/v1/messages

# Start app in background with job queue disabled (no postgres-jobs DB in test)
JOB_QUEUE_ENABLED=false uv run uvicorn src.adapters.api.app:create_app --factory --host 0.0.0.0 --port 8000 &

# Wait for ready
sleep 3 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
```

## Tests

### 1. Mailpit is accessible and empty
expected: Mailpit API returns 200 with 0 messages after clearing inbox
command: |
  curl -s http://mailpit:8025/api/v1/messages | python -m json.tool
result: pass

### 2. Register a new user
expected: POST /auth/register returns 202 with a user_id field
command: |
  curl -s -X POST http://localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"uat-test@example.com","password":"SecurePass123#","display_name":"UAT Tester"}' | python -m json.tool
result: pass

### 3. Verification email appears in Mailpit
expected: Mailpit API shows 1 message to uat-test@example.com with subject containing "Verify" or "verify". The email body contains a verification link with a token.
command: |
  sleep 2
  curl -s http://mailpit:8025/api/v1/messages | python -m json.tool
result: pass
note: Required restarting app with JOB_QUEUE_DATABASE_URL pointing to postgres:5432/jobs (postgres-jobs container not available). After fix, email arrived in Mailpit within 3 seconds.

### 4. Verification email has correct content
expected: Email has both HTML and plain text parts. HTML contains a link with /auth/verify?token=... The token is a valid itsdangerous signed value.
result: pass

### 5. Verify email endpoint works with token
expected: Extracting the token from the verification link and calling GET /auth/verify?token=TOKEN returns 200 with verified=true or similar success response.
result: pass

### 6. Verified user can log in
expected: POST /auth/token with the registered email/password returns 200 with an access_token.
result: pass

### 7. Full test suite passes
expected: All 444+ tests pass with no failures.
result: pass
note: 444 passed in 22.91s

### 8. Async chain is correct
expected: event_bus.publish, publish_all, on_user_registered, UoW.commit, and AuthService.register are all async coroutine functions.
result: pass

## Summary

total: 8
passed: 8
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Database connection strings should be in a .env file for easy override without modifying docker-compose.yml"
  status: failed
  reason: "JOB_QUEUE_DATABASE_URL, DATABASE_URL, DATABASE_URL_SYNC are hardcoded in docker-compose.yml. No .env file exists. Had to use inline env var override to point JOB_QUEUE_DATABASE_URL to postgres:5432/jobs when postgres-jobs container is unavailable."
  severity: minor
  test: 3
  root_cause: "Connection strings hardcoded in docker-compose.yml instead of .env file"
  artifacts:
    - path: "docker-compose.yml"
      issue: "Hardcoded DATABASE_URL, JOB_QUEUE_DATABASE_URL in environment section"
  missing:
    - "Create .env file with all connection strings"
    - "Reference .env from docker-compose.yml via env_file or variable interpolation"
  debug_session: ""
