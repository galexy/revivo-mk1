"""User aggregate root for authentication and identity.

User handles authentication (email, password) and belongs to a Household
for data scoping. The domain model stores password_hash but does NOT
perform hashing - that's an infrastructure concern (security adapter).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from .entity_id import HouseholdId, UserId


@dataclass(eq=False)
class User:
    """User aggregate root.

    Handles authentication and household membership.

    Attributes:
        id: Unique user identifier
        email: Login identifier (unique, normalized to lowercase)
        display_name: User's display name
        password_hash: Argon2 password hash (set by infrastructure)
        household_id: Household this user belongs to
        role: User role within household ("owner" or "member")
        email_verified: Whether email has been verified
        email_verified_at: When email was verified (None if not verified)
        created_at: When user was created
        updated_at: Last modification timestamp
    """

    id: UserId
    email: str
    display_name: str
    password_hash: str
    household_id: HouseholdId
    role: str = "member"
    email_verified: bool = False
    email_verified_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Collected domain events (cleared after persistence)
    _events: list = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def create(
        cls,
        email: str,
        display_name: str,
        password_hash: str,
        household_id: HouseholdId,
        role: str = "owner",
    ) -> Self:
        """Create a new user.

        Email is normalized to lowercase. Password hashing must be done
        by the caller (infrastructure concern).

        Args:
            email: User's email address (will be lowercased and stripped)
            display_name: User's display name (will be stripped)
            password_hash: Pre-hashed password (Argon2)
            household_id: Household this user belongs to
            role: User role ("owner" for registration, "member" for invites)

        Returns:
            New User instance with generated ID and UserRegistered event
        """
        from domain.events.user_events import UserRegistered

        now = datetime.now(UTC)
        user = cls(
            id=UserId.generate(),
            email=email.lower().strip(),
            display_name=display_name.strip(),
            password_hash=password_hash,
            household_id=household_id,
            role=role,
            email_verified=False,
            email_verified_at=None,
            created_at=now,
            updated_at=now,
        )
        user._events.append(
            UserRegistered(
                user_id=str(user.id),
                email=user.email,
                household_id=str(household_id),
                occurred_at=now,
            )
        )
        return user

    def verify_email(self) -> None:
        """Mark email as verified.

        Idempotent: calling on already-verified user is a no-op.
        Emits EmailVerified event only on first verification.
        """
        from domain.events.user_events import EmailVerified

        if self.email_verified:
            return  # Already verified, no-op

        now = datetime.now(UTC)
        self.email_verified = True
        self.email_verified_at = now
        self.updated_at = now
        self._events.append(
            EmailVerified(
                user_id=str(self.id),
                email=self.email,
                occurred_at=now,
            )
        )

    def update_display_name(self, name: str) -> None:
        """Update user's display name."""
        self.display_name = name.strip()
        self.updated_at = datetime.now(UTC)

    def collect_events(self) -> list:
        """Return and clear collected domain events.

        Events are returned as a list and the internal list is cleared.
        This follows the pattern where events are collected after
        persistence to ensure they're only processed once.
        """
        events = self._events.copy()
        self._events.clear()
        return events
