"""Refresh token repository using SQLAlchemy Core.

Refresh tokens are NOT domain aggregates. They are security infrastructure
records managed via SQLAlchemy Core (insert/select/update/delete statements)
executed through self._session.execute().

Token values are hashed with SHA-256 before storage. Raw tokens are never
persisted -- only the caller (AuthService) sees the raw value.

Token rotation uses a family-based approach:
- Each login creates a new token family (UUID)
- Each refresh rotates within the same family
- If a revoked token is reused, the ENTIRE family is revoked (theft detection)
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, delete, select, update
from sqlalchemy.orm import Session

from src.adapters.persistence.orm.tables import refresh_tokens
from src.domain.model.entity_id import UserId

REFRESH_TOKEN_EXPIRE_DAYS = 7


@dataclass
class RefreshTokenRecord:
    """Internal record representing a stored refresh token.

    This is NOT a domain entity. It's a data transfer object for
    the refresh token infrastructure.

    Attributes:
        id: Database primary key (auto-increment integer)
        user_id: String representation of the owning user's ID
        token_hash: SHA-256 hash of the raw token
        token_family: UUID identifying the token rotation chain
        expires_at: When this token expires
        created_at: When this token was created
        revoked_at: When this token was revoked (None if active)
    """

    id: int
    user_id: str
    token_hash: str
    token_family: str
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None


def _hash_token(raw_token: str) -> str:
    """Hash a raw token with SHA-256 for storage.

    Args:
        raw_token: The raw token string to hash.

    Returns:
        Hex-encoded SHA-256 hash of the token.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class RefreshTokenRepository:
    """SQLAlchemy Core implementation for refresh token persistence.

    Refresh tokens are NOT domain aggregates. They are security infrastructure
    records managed via SQLAlchemy Core (insert/select/update/delete statements)
    executed through self._session.execute().

    Token values are hashed with SHA-256 before storage. Raw tokens are never
    persisted -- only the caller (AuthService) sees the raw value.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def create_token(
        self, user_id: UserId, family: str | None = None
    ) -> tuple[str, RefreshTokenRecord]:
        """Create a new refresh token for a user.

        Generates a cryptographically random token via secrets.token_urlsafe(32),
        hashes it with SHA-256, and inserts a row into refresh_tokens table.

        Args:
            user_id: The user this token belongs to.
            family: Token family ID for rotation tracking. If None, generates a new
                    family (used for initial login). Subsequent rotations pass the
                    existing family to maintain the chain.

        Returns:
            Tuple of (raw_token, RefreshTokenRecord). The raw_token is returned
            ONLY here -- it is never stored. The record contains the hashed version.

        SQL equivalent:
            INSERT INTO refresh_tokens (user_id, token_hash, token_family, expires_at, created_at)
            VALUES (:user_id, :token_hash, :family, :expires_at, :now)
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_token(raw_token)
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        token_family = family or str(uuid.uuid4())

        result = self._session.execute(
            refresh_tokens.insert()
            .values(
                user_id=str(user_id),
                token_hash=token_hash,
                token_family=token_family,
                expires_at=expires_at,
                created_at=now,
                revoked_at=None,
            )
            .returning(refresh_tokens.c.id)
        )
        token_id = result.scalar_one()

        record = RefreshTokenRecord(
            id=token_id,
            user_id=str(user_id),
            token_hash=token_hash,
            token_family=token_family,
            expires_at=expires_at,
            created_at=now,
            revoked_at=None,
        )
        return raw_token, record

    def validate_and_rotate(
        self, raw_token: str
    ) -> tuple[str, RefreshTokenRecord] | None:
        """Validate a refresh token and rotate it (issue new token, revoke old).

        Looks up the token by its SHA-256 hash. If found, checks:
        1. Token is not revoked (revoked_at IS NULL)
        2. Token is not expired (expires_at > now)

        If the token is revoked (reuse detected), revokes the ENTIRE family
        as a security measure (potential token theft).

        If valid, revokes the old token and creates a new one in the same family.

        Args:
            raw_token: The raw token value from the client cookie.

        Returns:
            Tuple of (new_raw_token, new_record) on success, or None if invalid.

        SQL for lookup:
            SELECT * FROM refresh_tokens WHERE token_hash = :hash

        SQL for revoke old:
            UPDATE refresh_tokens SET revoked_at = :now WHERE id = :id

        SQL for family revocation (on reuse):
            UPDATE refresh_tokens SET revoked_at = :now
            WHERE token_family = :family AND revoked_at IS NULL
        """
        token_hash = _hash_token(raw_token)
        now = datetime.now(UTC)

        # Look up token by hash
        result = self._session.execute(
            select(refresh_tokens).where(refresh_tokens.c.token_hash == token_hash)
        )
        row = result.mappings().first()
        if row is None:
            return None

        # If already revoked -> reuse detected, revoke entire family
        if row["revoked_at"] is not None:
            self.revoke_family(row["token_family"])
            return None

        # If expired -> return None
        if row["expires_at"] <= now:
            return None

        # Revoke old token
        self._session.execute(
            update(refresh_tokens)
            .where(refresh_tokens.c.id == row["id"])
            .values(revoked_at=now)
        )

        # Create new token in same family
        return self.create_token(
            UserId.from_string(row["user_id"]),
            family=row["token_family"],
        )

    def revoke_all_for_user(self, user_id: UserId) -> int:
        """Revoke all active refresh tokens for a user (logout all sessions).

        Args:
            user_id: The user whose tokens to revoke.

        Returns:
            Number of tokens revoked.

        SQL:
            UPDATE refresh_tokens SET revoked_at = :now
            WHERE user_id = :user_id AND revoked_at IS NULL
        """
        now = datetime.now(UTC)
        result = self._session.execute(
            update(refresh_tokens)
            .where(
                and_(
                    refresh_tokens.c.user_id == str(user_id),
                    refresh_tokens.c.revoked_at.is_(None),
                )
            )
            .values(revoked_at=now)
        )
        return result.rowcount

    def revoke_family(self, family: str) -> int:
        """Revoke all tokens in a family (reuse detection response).

        When a revoked token is presented, this indicates potential theft.
        Revoke ALL tokens in the family to force re-authentication.

        Args:
            family: The token_family identifier.

        Returns:
            Number of tokens revoked.

        SQL:
            UPDATE refresh_tokens SET revoked_at = :now
            WHERE token_family = :family AND revoked_at IS NULL
        """
        now = datetime.now(UTC)
        result = self._session.execute(
            update(refresh_tokens)
            .where(
                and_(
                    refresh_tokens.c.token_family == family,
                    refresh_tokens.c.revoked_at.is_(None),
                )
            )
            .values(revoked_at=now)
        )
        return result.rowcount

    def cleanup_expired(self, older_than_days: int = 30) -> int:
        """Delete expired tokens older than the specified number of days.

        Removes fully expired tokens from the database to prevent table bloat.
        Only deletes tokens that expired more than `older_than_days` ago
        (keeps recent expired tokens for audit trail).

        Args:
            older_than_days: Delete tokens expired more than this many days ago.

        Returns:
            Number of tokens deleted.

        SQL:
            DELETE FROM refresh_tokens
            WHERE expires_at < :cutoff
        """
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        result = self._session.execute(
            delete(refresh_tokens).where(refresh_tokens.c.expires_at < cutoff)
        )
        return result.rowcount
