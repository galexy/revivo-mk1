"""SQLAlchemy implementation of AccountRepository.

Handles persistence of Account aggregate with value object reconstruction.
Value objects (Money, InstitutionDetails, RewardsBalance) are stored as
primitive columns and reconstructed when loading from database.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.exceptions import EntityNotFoundError
from domain.model.account import Account
from domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from domain.model.entity_id import AccountId, HouseholdId, UserId
from domain.model.institution import InstitutionDetails
from domain.model.money import Money
from domain.model.rewards_balance import RewardsBalance


class SqlAlchemyAccountRepository:
    """SQLAlchemy implementation of AccountRepository.

    Handles value object reconstruction when loading from database.
    SQLAlchemy loads primitive values; this repository converts them
    back to domain value objects.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def add(self, account: Account) -> None:
        """Add account to session for persistence.

        Value objects are automatically converted to primitives by SQLAlchemy
        because we map to primitive columns. The mapper handles the conversion
        via attribute access on the Account instance.

        Args:
            account: Account entity to persist.
        """
        self._session.add(account)

    def get(self, account_id: AccountId) -> Account | None:
        """Get account by ID, or None if not found.

        Args:
            account_id: The account identifier.

        Returns:
            Account entity with reconstructed value objects, or None.
        """
        account = self._session.get(Account, str(account_id))
        if account is not None:
            self._reconstruct_value_objects(account)
        return account

    def get_or_raise(self, account_id: AccountId) -> Account:
        """Get account by ID, raise EntityNotFoundError if not found.

        Args:
            account_id: The account identifier.

        Returns:
            Account entity with reconstructed value objects.

        Raises:
            EntityNotFoundError: If account doesn't exist.
        """
        account = self.get(account_id)
        if account is None:
            raise EntityNotFoundError(
                "Account not found",
                context={"account_id": str(account_id)},
            )
        return account

    def get_by_user(
        self,
        user_id: UserId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a user with optional filters.

        Args:
            user_id: The user identifier.
            status: Optional filter by account status.
            account_type: Optional filter by account type.

        Returns:
            List of Account entities with reconstructed value objects.
        """
        # Note: Account.user_id is stored as string in database
        stmt = select(Account).where(Account.user_id == str(user_id))

        if status is not None:
            stmt = stmt.where(Account.status == status.value)
        if account_type is not None:
            stmt = stmt.where(Account.account_type == account_type.value)

        stmt = stmt.order_by(Account.sort_order, Account.name)

        result = self._session.execute(stmt)
        accounts = list(result.scalars().all())

        for account in accounts:
            self._reconstruct_value_objects(account)

        return accounts

    def get_by_household(
        self,
        household_id: HouseholdId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a household with optional filters.

        Args:
            household_id: The household identifier for data scoping.
            status: Optional filter by account status.
            account_type: Optional filter by account type.

        Returns:
            List of Account entities with reconstructed value objects.
        """
        stmt = select(Account).where(Account.household_id == str(household_id))

        if status is not None:
            stmt = stmt.where(Account.status == status.value)
        if account_type is not None:
            stmt = stmt.where(Account.account_type == account_type.value)

        stmt = stmt.order_by(Account.sort_order, Account.name)

        result = self._session.execute(stmt)
        accounts = list(result.scalars().all())

        for account in accounts:
            self._reconstruct_value_objects(account)

        return accounts

    def delete(self, account: Account) -> None:
        """Delete account from session.

        Args:
            account: Account entity to delete.
        """
        self._session.delete(account)

    def has_transactions(self, account_id: AccountId) -> bool:
        """Check if account has any transactions.

        Note: Transactions table is added in Phase 3.
        For now, always returns False (accounts can be deleted).

        Args:
            account_id: The account identifier.

        Returns:
            True if account has transactions, False otherwise.

        TODO: Implement in Phase 3 when transactions table exists.
        """
        return False

    def _reconstruct_value_objects(self, account: Account) -> None:
        """Reconstruct value objects from database primitives.

        SQLAlchemy loads primitive column values. This method converts
        them back to domain value objects (Money, InstitutionDetails, etc.).

        Uses object.__setattr__ to bypass SQLAlchemy instrumentation
        and ensure domain value objects are properly reconstructed.

        Args:
            account: Account entity loaded from database.
        """
        # Reconstruct AccountId and UserId from strings
        if isinstance(account.id, str):
            object.__setattr__(account, "id", AccountId.from_string(account.id))
        if isinstance(account.user_id, str):
            object.__setattr__(account, "user_id", UserId.from_string(account.user_id))

        # Reconstruct HouseholdId from string
        if hasattr(account, "household_id") and isinstance(account.household_id, str):
            object.__setattr__(
                account, "household_id", HouseholdId.from_string(account.household_id)
            )

        # Reconstruct enums from string values
        if isinstance(account.account_type, str):
            object.__setattr__(
                account, "account_type", AccountType(account.account_type)
            )
        if isinstance(account.status, str):
            object.__setattr__(account, "status", AccountStatus(account.status))
        if account.subtype is not None and isinstance(account.subtype, str):
            object.__setattr__(account, "subtype", AccountSubtype(account.subtype))

        # Reconstruct created_by and updated_by UserId
        if account.created_by is not None and isinstance(account.created_by, str):
            object.__setattr__(
                account, "created_by", UserId.from_string(account.created_by)
            )
        if account.updated_by is not None and isinstance(account.updated_by, str):
            object.__setattr__(
                account, "updated_by", UserId.from_string(account.updated_by)
            )

        # Reconstruct Money - opening_balance (required field)
        # SQLAlchemy maps to opening_balance_amount and opening_balance_currency columns
        # but Account dataclass has opening_balance field, so we need to handle the
        # mapping between the flat columns and the value object.
        opening_amount = getattr(account, "opening_balance_amount", None)
        opening_currency = getattr(account, "opening_balance_currency", None)
        if opening_amount is not None and opening_currency is not None:
            object.__setattr__(
                account,
                "opening_balance",
                Money(Decimal(str(opening_amount)), opening_currency),
            )
        elif isinstance(account.opening_balance, Money):
            # Already a Money object, nothing to do
            pass
        elif account.opening_balance is not None:
            # Might be a Decimal if mapper set it directly, wrap in Money
            # This shouldn't normally happen with proper mapping
            pass

        # Reconstruct Money - credit_limit (optional, for credit cards)
        credit_amount = getattr(account, "credit_limit_amount", None)
        credit_currency = getattr(account, "credit_limit_currency", None)
        if credit_amount is not None and credit_currency is not None:
            object.__setattr__(
                account,
                "credit_limit",
                Money(Decimal(str(credit_amount)), credit_currency),
            )

        # Reconstruct InstitutionDetails (optional)
        institution_name = getattr(account, "institution_name", None)
        if institution_name is not None:
            institution = InstitutionDetails(
                name=institution_name,
                website=getattr(account, "institution_website", None),
                phone=getattr(account, "institution_phone", None),
                notes=getattr(account, "institution_notes", None),
            )
            object.__setattr__(account, "institution", institution)

        # Reconstruct RewardsBalance (optional, for rewards accounts)
        rewards_value = getattr(account, "rewards_value", None)
        rewards_unit = getattr(account, "rewards_unit", None)
        if rewards_value is not None and rewards_unit is not None:
            object.__setattr__(
                account,
                "rewards_balance",
                RewardsBalance(Decimal(str(rewards_value)), rewards_unit),
            )

        # Ensure _events list exists (transient field, not loaded from DB)
        if not hasattr(account, "_events") or getattr(account, "_events", None) is None:
            object.__setattr__(account, "_events", [])
