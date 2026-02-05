---
phase: 04-authentication-infrastructure
plan: 02
subsystem: auth
tags: [argon2, jwt, pyjwt, pwdlib, itsdangerous, password-hashing, token-verification]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Security adapter module structure (src/adapters/security/)
provides:
  - Password hashing with Argon2 via pwdlib
  - JWT access token creation and validation via PyJWT
  - Email verification token generation and validation via itsdangerous
  - TokenError exception for JWT validation failures
affects: [04-03, 04-04, 04-05, 04-06, 04-07, 04-08]

# Tech tracking
tech-stack:
  added: [PyJWT 2.11.x, pwdlib 0.3.x, argon2-cffi, itsdangerous 2.2.x, python-multipart]
  patterns: [TDD red-green for security primitives, environment-based secret configuration]

key-files:
  created:
    - src/adapters/security/password.py
    - src/adapters/security/jwt.py
    - src/adapters/security/tokens.py
    - tests/unit/adapters/security/test_password.py
    - tests/unit/adapters/security/test_jwt.py
    - tests/unit/adapters/security/test_tokens.py
  modified:
    - pyproject.toml
    - src/adapters/security/__init__.py

key-decisions:
  - "PyJWT over python-jose (abandoned, CVE-2025-61152)"
  - "pwdlib with Argon2 over passlib (deprecated, breaks Python 3.13+)"
  - "itsdangerous for email tokens (no DB lookup needed, signed+timestamped)"
  - "Explicit algorithm list in jwt.decode() to prevent algorithm confusion attack"
  - "JWT_SECRET from os.environ with fallback default for development"

patterns-established:
  - "Security modules as pure functions in adapters/security/ layer"
  - "TokenError exception class for JWT validation failures"
  - "TDD red-green cycle for security primitives"

# Metrics
duration: 4min
completed: 2026-02-05
---

# Phase 4 Plan 2: Security Primitives Summary

**Argon2 password hashing, JWT access tokens with PyJWT, and timed email verification tokens with itsdangerous -- 19 tests via TDD**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-05T02:48:47Z
- **Completed:** 2026-02-05T02:53:10Z
- **Tasks:** 7
- **Files modified:** 8

## Accomplishments
- Password hashing with Argon2 via pwdlib (unique salt per hash, constant-time verification)
- JWT access token creation with user_id, household_id, exp, iat claims
- JWT decoding with explicit algorithm list, required claims, and TokenError for failures
- Email verification tokens using itsdangerous (URL-safe, cryptographically signed, time-limited)
- Replaced python-jose with PyJWT (python-jose uninstalled automatically by uv)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add auth dependencies** - `fcf8485` (chore)
2. **Task 2: Write failing password tests** - `0501c45` (test)
3. **Task 3: Implement password hashing** - `96e882d` (feat)
4. **Task 4: Write failing JWT tests** - `dd4b674` (test)
5. **Task 5: Implement JWT functions** - `5702a84` (feat)
6. **Task 6: Write failing token tests** - `e25025b` (test)
7. **Task 7: Implement email verification tokens** - `dc09300` (feat)

_TDD tasks produced test -> impl commit pairs (tasks 2-3, 4-5, 6-7)_

## Files Created/Modified
- `pyproject.toml` - Added PyJWT, pwdlib[argon2], itsdangerous, python-multipart dependencies
- `src/adapters/security/password.py` - hash_password() and verify_password() using Argon2
- `src/adapters/security/jwt.py` - create_access_token() and decode_access_token() with PyJWT
- `src/adapters/security/tokens.py` - generate_verification_token() and verify_email_token() with itsdangerous
- `src/adapters/security/__init__.py` - Exports all security functions
- `tests/unit/adapters/security/test_password.py` - 5 tests for password hashing
- `tests/unit/adapters/security/test_jwt.py` - 8 tests for JWT functions
- `tests/unit/adapters/security/test_tokens.py` - 6 tests for email verification tokens

## Decisions Made
- **PyJWT over python-jose:** python-jose is abandoned (last release 2021) with CVE-2025-61152. PyJWT is FastAPI's current recommendation.
- **pwdlib with Argon2 over passlib:** passlib is deprecated and breaks on Python 3.13+ (crypt module removed). pwdlib is the recommended replacement.
- **itsdangerous for email tokens:** No database lookup needed -- token is self-contained with embedded email, signature, and timestamp.
- **Explicit algorithms in jwt.decode():** Always `algorithms=["HS256"]` to prevent algorithm confusion attacks.
- **JWT_SECRET from environment:** `os.environ.get("JWT_SECRET", "CHANGE-ME-IN-PRODUCTION")` with clear fallback for development.
- **Required claims in JWT:** `options={"require": ["exp", "sub", "household_id"]}` ensures tokens contain all necessary data.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed expired token test using max_age=-1**
- **Found during:** Task 7 (email verification token implementation)
- **Issue:** Test used `max_age=0` but itsdangerous considers a freshly-created token (age=0) valid with max_age=0
- **Fix:** Changed to `max_age=-1` which guarantees any token is considered expired
- **Files modified:** tests/unit/adapters/security/test_tokens.py
- **Verification:** Test passes reliably without timing dependency
- **Committed in:** dc09300 (Task 7 commit)

**2. [Rule 1 - Bug] Fixed lint errors in security modules**
- **Found during:** Task 7 (post-implementation verification)
- **Issue:** Missing exception chaining (`raise from`), unsorted imports, unused pytest imports
- **Fix:** Added `from e` to exception raises, sorted imports, removed unused imports
- **Files modified:** src/adapters/security/jwt.py, tests/unit/adapters/security/test_jwt.py, test_password.py, test_tokens.py
- **Verification:** `ruff check` passes clean
- **Committed in:** dc09300 (Task 7 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness and code quality. No scope creep.

## Issues Encountered
- python-jose was an existing dependency that got uninstalled when PyJWT was added (uv resolved the conflict). This is expected and desired -- python-jose should not be used.
- PyJWT warns about InsecureKeyLength when using the default fallback secret. This is expected in tests; production must set JWT_SECRET env var to a proper 32+ byte key.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Security primitives ready for auth service (Plan 04-05) and API routes (Plan 04-06)
- Password hashing ready for User entity registration flow
- JWT functions ready for login/token refresh endpoints
- Email verification tokens ready for registration verification flow
- All 237 unit tests pass (including 19 new security tests)
- Architecture contracts pass (domain has no infrastructure dependencies)

---
*Phase: 04-authentication-infrastructure*
*Completed: 2026-02-05*
