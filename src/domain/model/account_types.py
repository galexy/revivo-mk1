"""Account type enumerations.

Provides type-safe string enums for account classification:
- AccountType: The 7 supported account types
- AccountStatus: Account lifecycle states (active/closed)
- AccountSubtype: Optional subtypes for type-specific logic

Uses StrEnum (Python 3.11+) for direct string comparison and JSON serialization.
"""

from enum import StrEnum, auto


class AccountType(StrEnum):
    """Supported account types.

    These are the core account types supported by the system.
    Future specialized types (HSA, 529) should be built on these
    core types with additional hooks/rules.
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

    Accounts are either active (accepting transactions) or closed
    (preserved for history but no new transactions).
    """

    ACTIVE = auto()
    CLOSED = auto()


class AccountSubtype(StrEnum):
    """Optional subtypes for type-specific domain logic.

    Used to differentiate behavior within major account types:
    - IRA accounts may be Traditional, Roth, or SEP
    - Loan accounts may be Mortgage, Auto, Personal, or Line of Credit
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
