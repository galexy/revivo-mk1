"""Custom SQLAlchemy type decorators for domain types.

These type decorators handle conversion between domain value objects
and their database representations, enabling transparent persistence
of domain types like EntityIds and Enums.

"""
# pyright: reportMissingTypeArgument=false
# pyright: reportUnnecessaryIsInstance=false
# NOTE: reportMissingTypeArgument is suppressed because SQLAlchemy's TypeDecorator
# generic parameter is complex and not needed for correct runtime behavior.
# reportUnnecessaryIsInstance is suppressed because StrEnum subclasses are always
# str at the type level, but the isinstance checks are needed for runtime safety
# when values come from the database as plain strings.

from sqlalchemy import String
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator

from domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from domain.model.entity_id import (
    AccountId,
    CategoryId,
    HouseholdId,
    PayeeId,
    SplitId,
    TransactionId,
    UserId,
)
from domain.model.transaction_types import TransactionSource, TransactionStatus


class AccountIdType(TypeDecorator):
    """SQLAlchemy type for AccountId value objects.

    Converts AccountId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: AccountId | str | None, dialect: Dialect
    ) -> str | None:
        """Convert AccountId to string for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to AccountId done in repository."""
        return value


class UserIdType(TypeDecorator):
    """SQLAlchemy type for UserId value objects.

    Converts UserId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: UserId | str | None, dialect: Dialect
    ) -> str | None:
        """Convert UserId to string for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to UserId done in repository."""
        return value


class AccountTypeEnum(TypeDecorator):
    """SQLAlchemy type for AccountType enum.

    Converts AccountType to/from string value for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: AccountType | str | None, dialect: Dialect
    ) -> str | None:
        """Convert AccountType to string value for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.value

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to AccountType done in repository."""
        return value


class AccountStatusEnum(TypeDecorator):
    """SQLAlchemy type for AccountStatus enum.

    Converts AccountStatus to/from string value for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: AccountStatus | str | None, dialect: Dialect
    ) -> str | None:
        """Convert AccountStatus to string value for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.value

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to AccountStatus done in repository."""
        return value


class AccountSubtypeEnum(TypeDecorator):
    """SQLAlchemy type for AccountSubtype enum.

    Converts AccountSubtype to/from string value for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: AccountSubtype | str | None, dialect: Dialect
    ) -> str | None:
        """Convert AccountSubtype to string value for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.value

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to AccountSubtype done in repository."""
        return value


class TransactionIdType(TypeDecorator):
    """SQLAlchemy type for TransactionId value objects.

    Converts TransactionId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: TransactionId | str | None, dialect: Dialect
    ) -> str | None:
        """Convert TransactionId to string for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to TransactionId done in repository."""
        return value


class CategoryIdType(TypeDecorator):
    """SQLAlchemy type for CategoryId value objects.

    Converts CategoryId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: CategoryId | str | None, dialect: Dialect
    ) -> str | None:
        """Convert CategoryId to string for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to CategoryId done in repository."""
        return value


class PayeeIdType(TypeDecorator):
    """SQLAlchemy type for PayeeId value objects.

    Converts PayeeId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: PayeeId | str | None, dialect: Dialect
    ) -> str | None:
        """Convert PayeeId to string for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to PayeeId done in repository."""
        return value


class TransactionStatusEnum(TypeDecorator):
    """SQLAlchemy type for TransactionStatus enum.

    Converts TransactionStatus to/from string value for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: TransactionStatus | str | None, dialect: Dialect
    ) -> str | None:
        """Convert TransactionStatus to string value for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.value

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to TransactionStatus done in repository."""
        return value


class TransactionSourceEnum(TypeDecorator):
    """SQLAlchemy type for TransactionSource enum.

    Converts TransactionSource to/from string value for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: TransactionSource | str | None, dialect: Dialect
    ) -> str | None:
        """Convert TransactionSource to string value for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.value

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to TransactionSource done in repository."""
        return value


class SplitIdType(TypeDecorator):
    """SQLAlchemy type for SplitId value objects.

    Converts SplitId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: SplitId | str | None, dialect: Dialect
    ) -> str | None:
        """Convert SplitId to string for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to SplitId done in repository."""
        return value


class HouseholdIdType(TypeDecorator):
    """SQLAlchemy type for HouseholdId value objects.

    Converts HouseholdId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: HouseholdId | str | None, dialect: Dialect
    ) -> str | None:
        """Convert HouseholdId to string for database storage."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """Return string value - conversion to HouseholdId done in repository."""
        return value
