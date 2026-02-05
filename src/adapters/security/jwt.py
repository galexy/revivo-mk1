"""JWT token creation and validation using PyJWT.

Access tokens are short-lived (15 min) and contain user_id + household_id.
Refresh tokens are handled separately (stored in database, not stateless JWT).

IMPORTANT: Do NOT use python-jose (abandoned, has CVE-2025-61152).
CRITICAL: Always specify algorithms explicitly to prevent algorithm confusion attacks.
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

# Configuration from environment
JWT_SECRET = os.environ.get("JWT_SECRET", "CHANGE-ME-IN-PRODUCTION")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


class TokenError(Exception):
    """Raised when token validation fails."""


def create_access_token(
    user_id: str,
    household_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Token payload includes:
    - sub: user_id (standard JWT subject claim)
    - household_id: for data scoping
    - exp: expiration timestamp
    - iat: issued at timestamp

    Args:
        user_id: User identifier (string form of UserId)
        household_id: Household identifier (string form of HouseholdId)
        expires_delta: Optional custom expiry (defaults to 15 minutes)

    Returns:
        Encoded JWT string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(UTC)
    expire = now + expires_delta

    to_encode: dict[str, Any] = {
        "sub": user_id,
        "household_id": household_id,
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT string to decode

    Returns:
        Decoded payload dict with sub, household_id, exp, iat

    Raises:
        TokenError: If token is invalid, expired, or missing required claims
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],  # CRITICAL: explicit algorithm list
            options={"require": ["exp", "sub", "household_id"]},
        )
        return payload
    except ExpiredSignatureError:
        raise TokenError("Token has expired")
    except InvalidTokenError as e:
        raise TokenError(f"Invalid token: {e}")
