"""Transaction type enumerations.

Provides type-safe string enums for transaction classification:
- TransactionStatus: Status progression (PENDING -> CLEARED -> RECONCILED)
- TransactionSource: Origin of transaction (MANUAL vs DOWNLOADED)

All enums use StrEnum (Python 3.11+) for direct string comparison
and JSON-friendly serialization.
"""

from enum import StrEnum, auto


class TransactionStatus(StrEnum):
    """Transaction status progression.

    Status values representing the lifecycle of a transaction:
    - PENDING: Default for new transactions, not yet cleared
    - CLEARED: Posted/cleared to the account
    - RECONCILED: Verified against bank statement
    """

    PENDING = auto()
    CLEARED = auto()
    RECONCILED = auto()


class TransactionSource(StrEnum):
    """Source of transaction creation.

    Indicates how a transaction was created for Phase 6 linking model:
    - MANUAL: User-entered transaction
    - DOWNLOADED: Imported from bank sync
    """

    MANUAL = auto()
    DOWNLOADED = auto()
