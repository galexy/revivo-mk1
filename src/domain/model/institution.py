"""InstitutionDetails value object for financial institution metadata.

InstitutionDetails captures metadata about the financial institution where
an account is held. It's a composite value object that includes name,
website, phone, and notes.

Key design decisions:
- Immutable via frozen dataclass
- Name is required and cannot be empty/whitespace
- Website, phone, and notes are optional
- Creates new instance for any changes (value object pattern)
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstitutionDetails:
    """Immutable value object for financial institution details.

    Contains metadata about the institution where an account is held.
    Immutable - create new instance for changes.

    Args:
        name: Institution name (required, cannot be empty).
        website: Institution website URL (optional).
        phone: Institution phone number (optional).
        notes: Additional notes about the institution (optional).

    Examples:
        >>> bank = InstitutionDetails(
        ...     name="Chase Bank",
        ...     website="https://chase.com",
        ...     phone="1-800-935-9935"
        ... )
        >>> bank.name
        'Chase Bank'
    """

    name: str
    website: str | None = None
    phone: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize name."""
        # Validate name is not empty/whitespace
        if not self.name or not self.name.strip():
            raise ValueError("Institution name cannot be empty")

        # Normalize name by stripping whitespace
        # Use object.__setattr__ because frozen=True blocks normal assignment
        object.__setattr__(self, "name", self.name.strip())
