# Phase 4: Authentication Infrastructure - Research

**Researched:** 2026-02-04
**Domain:** JWT-based authentication with FastAPI, password hashing, email verification
**Confidence:** HIGH

## Summary

This research covers the standard stack and patterns for implementing JWT-based authentication in FastAPI. The ecosystem has evolved significantly: **python-jose is abandoned** (last release 2021, critical CVEs), **passlib is deprecated** (incompatible with Python 3.13+), and both FastAPI and FastAPI-Users have transitioned to **PyJWT** for token handling and **pwdlib with Argon2** for password hashing.

The canonical approach uses FastAPI's dependency injection with `OAuth2PasswordBearer` for token extraction, PyJWT for encoding/decoding, and pwdlib for secure password hashing. Refresh tokens should be stored in the database (hashed) with rotation on use, while access tokens remain stateless JWTs. The SPA-friendly pattern stores refresh tokens in HttpOnly cookies and access tokens in memory only.

**Primary recommendation:** Use PyJWT + pwdlib[argon2] + itsdangerous, following FastAPI's dependency injection pattern for authentication. Do NOT use python-jose (abandoned/vulnerable) or passlib (deprecated).

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | 2.11.x | JWT encoding/decoding | FastAPI's official recommendation, actively maintained, secure |
| pwdlib | 0.3.x | Password hashing | Replaces deprecated passlib, supports Argon2/bcrypt, FastAPI-recommended |
| argon2-cffi | 23.1.x | Argon2 implementation | Required by pwdlib[argon2], winner of Password Hashing Competition |
| itsdangerous | 2.x | URL-safe tokens | Timed tokens for email verification, Pallets project (maintained) |
| fastapi-mail | 1.6.x | Async email sending | SMTP/async support, Jinja2 templates, FastAPI integration |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | 0.0.x | Form parsing | Required for OAuth2PasswordRequestForm |
| email-validator | 2.x | Email validation | Already in Pydantic, validates email format |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyJWT | joserfc | If JWE (encrypted JWT) needed; more complex, less common |
| pwdlib | passlib | Only for legacy systems with existing bcrypt hashes; deprecated |
| fastapi-mail | SendGrid SDK | If using SendGrid API directly; more vendor lock-in |

**Installation:**
```bash
pip install PyJWT 'pwdlib[argon2]' itsdangerous fastapi-mail python-multipart
```

Or add to pyproject.toml:
```toml
dependencies = [
    # ... existing
    "PyJWT>=2.11.0",
    "pwdlib[argon2]>=0.3.0",
    "itsdangerous>=2.2.0",
    "fastapi-mail>=1.6.0",
    "python-multipart>=0.0.9",
]
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── domain/
│   └── model/
│       ├── user.py           # User entity (email, display_name, password_hash)
│       ├── household.py      # Household entity (name, owner relationship)
│       └── entity_id.py      # Add HouseholdId
├── adapters/
│   ├── api/
│   │   ├── routes/
│   │   │   └── auth.py       # /auth/* endpoints (register, login, refresh, verify)
│   │   ├── schemas/
│   │   │   └── auth.py       # Request/response schemas
│   │   └── dependencies.py   # get_current_user, OAuth2PasswordBearer
│   ├── persistence/
│   │   ├── orm/
│   │   │   └── tables.py     # Add users, households, refresh_tokens tables
│   │   └── repositories/
│   │       ├── user.py       # UserRepository
│   │       └── refresh_token.py  # RefreshTokenRepository
│   └── security/
│       ├── password.py       # Password hashing with pwdlib
│       ├── jwt.py            # JWT encode/decode with PyJWT
│       └── tokens.py         # Email verification tokens with itsdangerous
├── application/
│   └── services/
│       └── auth_service.py   # Registration, login, token refresh logic
```

### Pattern 1: FastAPI Dependency Injection for Authentication
**What:** Use `OAuth2PasswordBearer` + `Depends()` to inject authenticated user into routes
**When to use:** All protected routes
**Example:**
```python
# Source: FastAPI official documentation pattern
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dataclasses import dataclass
import jwt
from jwt.exceptions import InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@dataclass
class CurrentUser:
    """Minimal user context for request handling."""
    user_id: str
    household_id: str

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> CurrentUser:
    """Extract and validate user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]  # CRITICAL: Always specify algorithms explicitly
        )
        user_id: str = payload.get("sub")
        household_id: str = payload.get("household_id")
        if user_id is None or household_id is None:
            raise credentials_exception
        return CurrentUser(user_id=user_id, household_id=household_id)
    except InvalidTokenError:
        raise credentials_exception

# Usage in route
@router.get("/accounts")
async def list_accounts(
    current_user: CurrentUser = Depends(get_current_user)
) -> list[Account]:
    # current_user.household_id used to filter accounts
    ...
```

### Pattern 2: Refresh Token Rotation with Database Storage
**What:** Store hashed refresh tokens in database, rotate on use, detect reuse
**When to use:** Refresh token endpoint
**Example:**
```python
# Database schema for refresh tokens
refresh_tokens = Table(
    "refresh_tokens",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("token_hash", String(64), nullable=False, unique=True),  # SHA-256 hash
    Column("token_family", String(36), nullable=False),  # For reuse detection
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Index("ix_refresh_tokens_user_id", "user_id"),
    Index("ix_refresh_tokens_token_hash", "token_hash"),
    Index("ix_refresh_tokens_family", "token_family"),
)
```

### Pattern 3: HttpOnly Cookie for Refresh Token
**What:** Set refresh token as HttpOnly/Secure/SameSite cookie
**When to use:** Login and refresh endpoints
**Example:**
```python
# Source: FastAPI advanced cookies documentation pattern
from fastapi import Response

@router.post("/auth/token")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    # ... authenticate user ...

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="strict",  # Prevent CSRF
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/auth/refresh",  # Only sent to refresh endpoint
    )

    # Return access token in response body (stored in memory by SPA)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=900,  # 15 minutes
    )
```

### Pattern 4: Email Verification with Timed Tokens
**What:** Use itsdangerous URLSafeTimedSerializer for verification links
**When to use:** Registration flow
**Example:**
```python
# Source: itsdangerous documentation + Flask patterns
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def generate_verification_token(email: str) -> str:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt="email-verification")

def verify_email_token(token: str, max_age: int = 86400) -> str | None:
    """Verify token and return email, or None if invalid/expired."""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt="email-verification", max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None
```

### Anti-Patterns to Avoid
- **Storing access tokens in localStorage:** XSS vulnerable; use memory-only for SPAs
- **Using `algorithms` from token header:** Algorithm confusion attack; always specify explicitly
- **Returning different errors for invalid email vs wrong password:** Email enumeration; always "Invalid credentials"
- **Not hashing refresh tokens:** Stored tokens in DB must be hashed (SHA-256)
- **Using python-jose:** Abandoned, has critical CVEs (CVE-2025-61152 allows 'alg=none' bypass)
- **Using passlib with Python 3.13+:** crypt module removed, causes ImportError

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt wrapper | pwdlib[argon2] | Timing attacks, salt handling, work factor tuning |
| JWT signing | Custom token format | PyJWT with HS256 | Spec compliance, algorithm validation, claim verification |
| Email verification tokens | Random UUID in DB | itsdangerous timed serializer | Cryptographic signing, expiration built-in, no DB lookup |
| Form data parsing | Manual multipart | python-multipart + OAuth2PasswordRequestForm | FastAPI integration, OpenAPI docs auto-generation |
| Token extraction | Manual header parsing | OAuth2PasswordBearer | Standard Bearer format, auto 401, Swagger "Authorize" button |
| Password validation | Regex patterns | Pydantic validators with clear rules | Composable, testable, clear error messages |

**Key insight:** Security libraries exist because edge cases (timing attacks, algorithm confusion, signature malleability) are subtle and dangerous. Rolling custom auth is a common source of vulnerabilities.

## Common Pitfalls

### Pitfall 1: Algorithm Confusion Attack
**What goes wrong:** Attacker changes JWT header `alg` to bypass signature verification
**Why it happens:** Server trusts the algorithm specified in the token
**How to avoid:** Always pass `algorithms=["HS256"]` explicitly to `jwt.decode()`
**Warning signs:** Using `jwt.decode(token, key)` without `algorithms` parameter

### Pitfall 2: Refresh Token Reuse After Rotation
**What goes wrong:** Attacker uses stolen refresh token after legitimate user already refreshed
**Why it happens:** No tracking of token families or reuse detection
**How to avoid:** Store token_family UUID, invalidate all tokens in family on reuse detection
**Warning signs:** No database table for refresh tokens, or no family tracking

### Pitfall 3: Email Enumeration via Registration/Login
**What goes wrong:** Attacker discovers valid emails by observing different error messages
**Why it happens:** "Email already exists" vs "Invalid password" reveals email validity
**How to avoid:** Return generic "Invalid credentials" for all auth failures; registration always returns 202
**Warning signs:** Specific error codes like "USER_NOT_FOUND" vs "WRONG_PASSWORD"

### Pitfall 4: Access Token in localStorage
**What goes wrong:** XSS attack steals token, attacker has long-lived access
**Why it happens:** Convenient but insecure; persists across sessions
**How to avoid:** Access tokens in memory only; refresh tokens in HttpOnly cookies
**Warning signs:** `localStorage.setItem("access_token", ...)` in frontend code

### Pitfall 5: Missing Token Expiration Validation
**What goes wrong:** Expired tokens still accepted
**Why it happens:** PyJWT verifies `exp` by default, but custom implementations may skip it
**How to avoid:** Ensure `exp` claim is present and PyJWT's default verification is enabled
**Warning signs:** `options={"verify_exp": False}` in decode call

### Pitfall 6: Hardcoded or Weak JWT Secrets
**What goes wrong:** Attacker brute-forces secret, can forge any token
**Why it happens:** Using simple strings or checking into version control
**How to avoid:** Generate with `secrets.token_urlsafe(32)`, store in environment variable
**Warning signs:** `SECRET_KEY = "secret"` or secret in source code

## Code Examples

Verified patterns from official sources:

### Password Hashing with pwdlib
```python
# Source: pwdlib documentation + FastAPI-Users patterns
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Create password hasher (Argon2 recommended)
password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(plain_password: str) -> str:
    """Hash a password using Argon2."""
    return password_hash.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return password_hash.verify(plain_password, hashed_password)
```

### JWT Token Creation
```python
# Source: PyJWT documentation + FastAPI security patterns
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any

SECRET_KEY = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### JWT Token Decoding with Exception Handling
```python
# Source: PyJWT API reference
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],  # CRITICAL: explicit algorithm list
            options={"require": ["exp", "sub", "household_id"]}
        )
        return payload
    except ExpiredSignatureError:
        # Token expired - client should refresh
        return None
    except InvalidTokenError:
        # Malformed, invalid signature, missing claims, etc.
        return None
```

### HttpOnly Cookie Setting
```python
# Source: FastAPI Response Cookies documentation
from fastapi import Response

def set_refresh_token_cookie(response: Response, token: str) -> None:
    """Set refresh token as secure HttpOnly cookie."""
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        path="/auth/refresh",
    )

def clear_refresh_token_cookie(response: Response) -> None:
    """Clear refresh token cookie (logout)."""
    response.delete_cookie(
        key="refresh_token",
        path="/auth/refresh",
    )
```

### Reading Cookie in Route
```python
# Source: FastAPI Cookie Parameters documentation
from fastapi import Cookie, HTTPException, status

@router.post("/auth/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
) -> TokenResponse:
    """Refresh access token using refresh token from cookie."""
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    # Validate and rotate refresh token...
```

### Password Validation with Pydantic
```python
# Source: Pydantic validators pattern
from pydantic import BaseModel, field_validator
import re

class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity per CONTEXT.md requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain a symbol")
        return v
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose | PyJWT | 2024 (FastAPI docs update) | Must migrate; python-jose has unpatched CVEs |
| passlib + bcrypt | pwdlib + Argon2 | 2024 (crypt deprecation PEP 594) | passlib breaks on Python 3.13+; Argon2 is more secure |
| fastapi-users | Manual implementation | 2025 (maintenance mode) | Library stable but no new features; evaluate per-project |
| Access token in cookie | Access in memory, refresh in HttpOnly cookie | 2023+ | Better XSS protection for SPAs |

**Deprecated/outdated:**
- **python-jose**: Last release 2021, CVE-2025-61152 (alg=none bypass), do not use
- **passlib**: Uses deprecated crypt module, breaks on Python 3.13+
- **fastapi-jwt-auth**: Abandoned, superseded by manual PyJWT patterns

## Open Questions

Things that couldn't be fully resolved:

1. **Email service provider choice**
   - What we know: fastapi-mail supports any SMTP; SendGrid/Postmark/SES have APIs
   - What's unclear: Project's preferred provider (requires human decision)
   - Recommendation: Plan for SMTP config initially; provider-specific can be added later

2. **JWT RS256 vs HS256**
   - What we know: HS256 simpler (shared secret), RS256 supports key rotation
   - What's unclear: Whether multi-service deployment is expected
   - Recommendation: Start with HS256 per CONTEXT.md suggestion; RS256 if needed later

3. **Token blacklist storage**
   - What we know: Redis is common; database TTL works too
   - What's unclear: Whether Redis is in scope for Phase 4
   - Recommendation: Use database-based approach for now; Redis if performance requires

## Sources

### Primary (HIGH confidence)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/en/stable/usage.html) - Token encoding/decoding, exception handling
- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/) - OAuth2PasswordBearer, dependency injection
- [FastAPI Response Cookies](https://fastapi.tiangolo.com/advanced/response-cookies/) - HttpOnly cookie patterns
- [pwdlib Documentation](https://frankie567.github.io/pwdlib/) - Password hashing API
- [itsdangerous Documentation](https://palletsprojects.com/p/itsdangerous/) - Timed token serialization

### Secondary (MEDIUM confidence)
- [FastAPI-Users Password Hash](https://fastapi-users.github.io/fastapi-users/12.1/configuration/password-hash/) - pwdlib integration patterns
- [FastAPI JWT GitHub Discussion #9587](https://github.com/fastapi/fastapi/discussions/9587) - python-jose deprecation rationale
- [fastapi-mail PyPI](https://pypi.org/project/fastapi-mail/) - Email sending patterns
- [Auth0 Refresh Token Rotation Guide](https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/) - Token family pattern

### Tertiary (LOW confidence)
- Medium/blog posts on JWT best practices - General patterns verified against official docs
- GitHub Discussions on FastAPI security - Community patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official FastAPI recommendations, PyJWT/pwdlib docs verified
- Architecture: HIGH - Based on FastAPI dependency injection docs, widely adopted patterns
- Pitfalls: HIGH - CVEs documented, algorithm confusion is well-known attack
- Email verification: MEDIUM - itsdangerous is standard, but email provider choice varies

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - stable domain, but check for new CVEs)
