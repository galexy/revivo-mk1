"""Account type enumerations.

Provides type-safe string enums for account classification:
- AccountType: The 7 supported account types
- AccountStatus: Account lifecycle states (ACTIVE, CLOSED)
- AccountSubtype: Optional subtypes for type-specific domain logic

All enums use StrEnum (Python 3.11+) for direct string comparison
and JSON-friendly serialization.
"""

from enum import StrEnum, auto


class AccountType(StrEnum):
    """Supported account types.

    Each value represents a distinct category of financial account
    with its own validation rules and behavior.
    """

    CHECKING = auto()
    SAVINGS = auto()
    CREDIT_CARD = auto()
    LOAN = auto()
    BROKERAGE = auto()
    IRA = auto()
    REWARDS = auto()


class AccountStatus(StrEnum):
    """Account lifecycle status.

    Accounts start as ACTIVE and can be CLOSED. Closed accounts
    can be reopened, returning to ACTIVE status.
    """

    ACTIVE = auto()
    CLOSED = auto()


class AccountSubtype(StrEnum):
    """Optional subtypes for type-specific domain logic.

    Subtypes provide additional classification within a main account type.
    For example, IRA accounts can be Traditional, Roth, or SEP.
    """

    # IRA subtypes
    TRADITIONAL_IRA = auto()
    ROTH_IRA = auto()
    SEP_IRA = auto()

    # Loan subtypes
    MORTGAGE = auto()
    AUTO_LOAN = auto()
    PERSONAL_LOAN = auto()
    LINE_OF_CREDIT = auto()
