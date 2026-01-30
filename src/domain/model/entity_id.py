"""Prefixed entity identifiers (Stripe-style).

This module provides type-safe, human-readable entity identifiers with
prefixes that indicate the entity type. Based on TypeID specification
which uses UUID7 (time-sortable) with URL-safe base32 encoding.

Format examples:
- AccountId: acct_01h455vb4pex5vsknk084sn02q
- TransactionId: txn_01h455vb4pex5vsknk084sn02q
- UserId: user_01h455vb4pex5vsknk084sn02q

Key benefits:
- Human-readable: Prefix indicates entity type at a glance
- Time-sortable: UUID7-based, lexicographically sortable by creation time
- Type-safe: Separate classes prevent mixing different ID types
- URL-safe: Base32 encoding, no special characters
"""

from dataclasses import dataclass
from typing import Self

from typeid import TypeID


@dataclass(frozen=True, slots=True)
class EntityId:
    """Base class for prefixed entity identifiers.

    Not intended for direct instantiation - use specific ID types like
    AccountId, TransactionId, etc.

    Attributes:
        value: The full prefixed ID string (e.g., "acct_01h455vb4pex5vsknk084sn02q")
    """

    value: str

    @classmethod
    def generate(cls, prefix: str) -> "EntityId":
        """Generate a new ID with the given prefix.

        Args:
            prefix: Entity type prefix (e.g., "acct", "txn", "user")

        Returns:
            New EntityId with generated value.
        """
        tid = TypeID(prefix=prefix)
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> "EntityId":
        """Parse and validate an ID from string.

        Args:
            value: Full prefixed ID string to parse.

        Returns:
            EntityId with validated value.

        Raises:
            ValueError: If the ID format is invalid.
        """
        # TypeID validates format on parse
        TypeID.from_string(value)
        return cls(value=value)

    @property
    def prefix(self) -> str:
        """Extract the prefix from the ID value."""
        return self.value.split("_")[0]

    def __str__(self) -> str:
        """Return the full ID string for easy serialization."""
        return self.value


@dataclass(frozen=True, slots=True)
class AccountId:
    """Identifier for Account aggregate root.

    Format: acct_01h455vb4pex5vsknk084sn02q
    """

    value: str

    @classmethod
    def generate(cls) -> Self:
        """Generate a new AccountId."""
        tid = TypeID(prefix="acct")
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse and validate an AccountId from string.

        Args:
            value: Full prefixed ID string (must start with "acct_").

        Returns:
            AccountId with validated value.

        Raises:
            ValueError: If ID format is invalid or prefix doesn't match.
        """
        tid = TypeID.from_string(value)
        if tid.prefix != "acct":
            raise ValueError(f"Expected 'acct' prefix, got '{tid.prefix}'")
        return cls(value=value)

    @property
    def prefix(self) -> str:
        """Return the prefix (always 'acct')."""
        return "acct"

    def __str__(self) -> str:
        """Return the full ID string."""
        return self.value


@dataclass(frozen=True, slots=True)
class TransactionId:
    """Identifier for Transaction aggregate root.

    Format: txn_01h455vb4pex5vsknk084sn02q
    """

    value: str

    @classmethod
    def generate(cls) -> Self:
        """Generate a new TransactionId."""
        tid = TypeID(prefix="txn")
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse and validate a TransactionId from string.

        Args:
            value: Full prefixed ID string (must start with "txn_").

        Returns:
            TransactionId with validated value.

        Raises:
            ValueError: If ID format is invalid or prefix doesn't match.
        """
        tid = TypeID.from_string(value)
        if tid.prefix != "txn":
            raise ValueError(f"Expected 'txn' prefix, got '{tid.prefix}'")
        return cls(value=value)

    @property
    def prefix(self) -> str:
        """Return the prefix (always 'txn')."""
        return "txn"

    def __str__(self) -> str:
        """Return the full ID string."""
        return self.value


@dataclass(frozen=True, slots=True)
class UserId:
    """Identifier for User aggregate root.

    Format: user_01h455vb4pex5vsknk084sn02q
    """

    value: str

    @classmethod
    def generate(cls) -> Self:
        """Generate a new UserId."""
        tid = TypeID(prefix="user")
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse and validate a UserId from string.

        Args:
            value: Full prefixed ID string (must start with "user_").

        Returns:
            UserId with validated value.

        Raises:
            ValueError: If ID format is invalid or prefix doesn't match.
        """
        tid = TypeID.from_string(value)
        if tid.prefix != "user":
            raise ValueError(f"Expected 'user' prefix, got '{tid.prefix}'")
        return cls(value=value)

    @property
    def prefix(self) -> str:
        """Return the prefix (always 'user')."""
        return "user"

    def __str__(self) -> str:
        """Return the full ID string."""
        return self.value


@dataclass(frozen=True, slots=True)
class CategoryId:
    """Identifier for Category entity.

    Format: cat_01h455vb4pex5vsknk084sn02q
    """

    value: str

    @classmethod
    def generate(cls) -> Self:
        """Generate a new CategoryId."""
        tid = TypeID(prefix="cat")
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse and validate a CategoryId from string.

        Args:
            value: Full prefixed ID string (must start with "cat_").

        Returns:
            CategoryId with validated value.

        Raises:
            ValueError: If ID format is invalid or prefix doesn't match.
        """
        tid = TypeID.from_string(value)
        if tid.prefix != "cat":
            raise ValueError(f"Expected 'cat' prefix, got '{tid.prefix}'")
        return cls(value=value)

    @property
    def prefix(self) -> str:
        """Return the prefix (always 'cat')."""
        return "cat"

    def __str__(self) -> str:
        """Return the full ID string."""
        return self.value


@dataclass(frozen=True, slots=True)
class BudgetId:
    """Identifier for Budget aggregate root.

    Format: budg_01h455vb4pex5vsknk084sn02q
    """

    value: str

    @classmethod
    def generate(cls) -> Self:
        """Generate a new BudgetId."""
        tid = TypeID(prefix="budg")
        return cls(value=str(tid))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse and validate a BudgetId from string.

        Args:
            value: Full prefixed ID string (must start with "budg_").

        Returns:
            BudgetId with validated value.

        Raises:
            ValueError: If ID format is invalid or prefix doesn't match.
        """
        tid = TypeID.from_string(value)
        if tid.prefix != "budg":
            raise ValueError(f"Expected 'budg' prefix, got '{tid.prefix}'")
        return cls(value=value)

    @property
    def prefix(self) -> str:
        """Return the prefix (always 'budg')."""
        return "budg"

    def __str__(self) -> str:
        """Return the full ID string."""
        return self.value
