"""Password hashing infrastructure using Argon2.

Uses pwdlib with Argon2Hasher (winner of Password Hashing Competition).
This module is infrastructure - domain layer does not depend on it.

IMPORTANT: Do NOT use passlib (deprecated, breaks on Python 3.13+).
"""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Create password hasher with Argon2 (recommended by FastAPI-Users, pwdlib docs)
_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(plain_password: str) -> str:
    """Hash a password using Argon2.

    Args:
        plain_password: The plaintext password to hash.

    Returns:
        Argon2 hash string suitable for database storage.
    """
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The stored Argon2 hash.

    Returns:
        True if password matches, False otherwise.
    """
    return _password_hash.verify(plain_password, hashed_password)
