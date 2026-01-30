"""Custom SQLAlchemy type decorators for domain types.

These type decorators handle conversion between domain value objects
and their database representations, enabling transparent persistence
of domain types like EntityIds and Enums.
"""

from sqlalchemy import String
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator

from src.domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from src.domain.model.entity_id import AccountId, UserId


class AccountIdType(TypeDecorator):
    """SQLAlchemy type for AccountId value objects.

    Converts AccountId to/from string for database storage.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: AccountId | str | None, dialect: Dialect) -> str | None:
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

    def process_bind_param(self, value: UserId | str | None, dialect: Dialect) -> str | None:
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

    def process_bind_param(self, value: AccountType | str | None, dialect: Dialect) -> str | None:
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

    def process_bind_param(self, value: AccountStatus | str | None, dialect: Dialect) -> str | None:
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
