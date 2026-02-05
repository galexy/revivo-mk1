"""Timed token generation for email verification.

Uses itsdangerous URLSafeTimedSerializer for cryptographically signed,
time-limited tokens. No database lookup required - the token itself
contains the email and is validated by signature + timestamp.
"""

import os

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# Use same secret as JWT (or separate if needed)
TOKEN_SECRET = os.environ.get("JWT_SECRET", "CHANGE-ME-IN-PRODUCTION")
EMAIL_VERIFICATION_SALT = "email-verification"
EMAIL_VERIFICATION_MAX_AGE = 86400  # 24 hours in seconds


def generate_verification_token(email: str) -> str:
    """Generate a URL-safe verification token for email.

    Token is cryptographically signed and includes timestamp.
    Valid for 24 hours by default.

    Args:
        email: The email address to embed in token

    Returns:
        URL-safe token string (can be used in links)
    """
    serializer = URLSafeTimedSerializer(TOKEN_SECRET)
    return serializer.dumps(email, salt=EMAIL_VERIFICATION_SALT)


def verify_email_token(
    token: str, max_age: int = EMAIL_VERIFICATION_MAX_AGE
) -> str | None:
    """Verify an email verification token and extract the email.

    Args:
        token: The token to verify
        max_age: Maximum age in seconds (default 24 hours)

    Returns:
        The email address if token is valid, None if invalid/expired
    """
    serializer = URLSafeTimedSerializer(TOKEN_SECRET)
    try:
        email: str = serializer.loads(
            token, salt=EMAIL_VERIFICATION_SALT, max_age=max_age
        )
        return email
    except (SignatureExpired, BadSignature):
        return None
