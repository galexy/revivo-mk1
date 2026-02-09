"""SQLAlchemy implementation of AccountRepository.

Handles persistence of Account aggregate with EntityId/Enum reconstruction.
Value objects (Money, InstitutionDetails, RewardsBalance) are automatically
mapped via SQLAlchemy composite() and require no manual reconstruction.

NOTE: SQLAlchemy imperative mapping makes domain class attributes behave as
Column descriptors at runtime, but pyright sees them as their declared Python
types. The type: ignore comments on .where() and .order_by() clauses are
expected and correct.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.exceptions import EntityNotFoundError
from domain.model.account import Account
from domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from domain.model.entity_id import AccountId, HouseholdId, UserId


class SqlAlchemyAccountRepository:
    """SQLAlchemy implementation of AccountRepository.

    Handles EntityId and Enum reconstruction when loading from database.
    Value objects (Money, InstitutionDetails, RewardsBalance) are automatically
    mapped via composite() and require no manual handling.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with SQLAlchemy session.

        Args:
            session: Active SQLAlchemy session for database operations.
        """
        self._session = session

    def add(self, account: Account) -> None:
        """Add account to session for persistence.

        Args:
            account: Account entity to persist.
        """
        self._session.add(account)

    def get(self, account_id: AccountId) -> Account | None:
        """Get account by ID, or None if not found.

        Args:
            account_id: The account identifier.

        Returns:
            Account entity with reconstructed EntityIds and Enums, or None.
        """
        account = self._session.get(Account, str(account_id))
        if account is not None:
            self._reconstruct_entity_ids_and_enums(account)
        return account

    def get_or_raise(self, account_id: AccountId) -> Account:
        """Get account by ID, raise EntityNotFoundError if not found.

        Args:
            account_id: The account identifier.

        Returns:
            Account entity with reconstructed EntityIds and Enums.

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
            List of Account entities with reconstructed EntityIds and Enums.
        """
        # Note: Account.user_id is stored as string in database
        stmt = select(Account).where(
            Account.user_id == str(user_id)  # type: ignore[arg-type]  # SQLAlchemy imperative mapping: domain attr becomes Column at runtime
        )

        if status is not None:
            stmt = stmt.where(
                Account.status == status.value  # type: ignore[arg-type]  # SQLAlchemy imperative mapping
            )
        if account_type is not None:
            stmt = stmt.where(
                Account.account_type == account_type.value  # type: ignore[arg-type]  # SQLAlchemy imperative mapping
            )

        stmt = stmt.order_by(Account.sort_order, Account.name)  # type: ignore[arg-type]  # SQLAlchemy imperative mapping: int/str attrs become Column at runtime

        result = self._session.execute(stmt)
        accounts = list(result.scalars().all())

        for account in accounts:
            self._reconstruct_entity_ids_and_enums(account)

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
            List of Account entities with reconstructed EntityIds and Enums.
        """
        stmt = select(Account).where(
            Account.household_id == str(household_id)  # type: ignore[arg-type]  # SQLAlchemy imperative mapping: domain attr becomes Column at runtime
        )

        if status is not None:
            stmt = stmt.where(
                Account.status == status.value  # type: ignore[arg-type]  # SQLAlchemy imperative mapping
            )
        if account_type is not None:
            stmt = stmt.where(
                Account.account_type == account_type.value  # type: ignore[arg-type]  # SQLAlchemy imperative mapping
            )

        stmt = stmt.order_by(Account.sort_order, Account.name)  # type: ignore[arg-type]  # SQLAlchemy imperative mapping: int/str attrs become Column at runtime

        result = self._session.execute(stmt)
        accounts = list(result.scalars().all())

        for account in accounts:
            self._reconstruct_entity_ids_and_enums(account)

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

    def _reconstruct_entity_ids_and_enums(self, account: Account) -> None:
        """Reconstruct EntityIds and Enums from database strings.

        TypeDecorators return strings from the database. This method converts
        them to domain types (EntityIds and Enums).

        Value objects (Money, InstitutionDetails, RewardsBalance) are
        automatically handled by composite() mappings and don't need
        reconstruction here.

        Args:
            account: Account entity loaded from database.
        """
        # Reconstruct AccountId and UserId from strings
        if isinstance(account.id, str):  # type: ignore[arg-type]  # SQLAlchemy loads str from DB, isinstance narrows for reconstruction
            object.__setattr__(account, "id", AccountId.from_string(account.id))  # type: ignore[arg-type]  # str at runtime from DB
        if isinstance(account.user_id, str):  # type: ignore[arg-type]  # SQLAlchemy loads str from DB
            object.__setattr__(account, "user_id", UserId.from_string(account.user_id))  # type: ignore[arg-type]  # str at runtime from DB

        # Reconstruct HouseholdId from string
        if hasattr(account, "household_id") and isinstance(account.household_id, str):  # type: ignore[arg-type]  # SQLAlchemy loads str from DB
            object.__setattr__(
                account,
                "household_id",
                HouseholdId.from_string(account.household_id),  # type: ignore[arg-type]  # str at runtime from DB
            )

        # Reconstruct enums from string values
        if isinstance(account.account_type, str):  # type: ignore[arg-type]  # SQLAlchemy loads str from DB
            object.__setattr__(
                account, "account_type", AccountType(account.account_type)
            )
        if isinstance(account.status, str):  # type: ignore[arg-type]  # SQLAlchemy loads str from DB
            object.__setattr__(account, "status", AccountStatus(account.status))
        if account.subtype is not None and isinstance(account.subtype, str):  # type: ignore[arg-type]  # SQLAlchemy loads str from DB
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

        # Ensure _events list exists (transient field, not loaded from DB)
        if not hasattr(account, "_events") or getattr(account, "_events", None) is None:
            object.__setattr__(account, "_events", [])
