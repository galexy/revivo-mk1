"""AccountService application service for account use case orchestration.

This service coordinates domain operations for accounts, managing transaction
boundaries and event collection through the Unit of Work pattern.

Key responsibilities:
- Create accounts of all 7 types
- Retrieve accounts by ID or user
- Lifecycle operations (close, reopen, delete)
- Property updates (name)
- Event collection before commit

Design decisions:
- Uses UnitOfWork for transaction boundaries
- Returns AccountError for failures instead of raising exceptions
- Collects events before commit for outbox pattern
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from domain.events.account_events import AccountDeleted
from domain.model.account import Account
from domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from domain.model.entity_id import AccountId, HouseholdId, UserId
from domain.model.institution import InstitutionDetails
from domain.model.money import Money
from domain.model.rewards_balance import RewardsBalance

if TYPE_CHECKING:
    from domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class AccountError:
    """Error result for account operations.

    Used instead of exceptions for expected failures.
    The API layer can convert these to appropriate HTTP responses.

    Attributes:
        code: Machine-readable error code (e.g., "NOT_FOUND", "HAS_TRANSACTIONS")
        message: Human-readable error message
    """

    code: str
    message: str


class AccountService:
    """Application service for account use cases.

    Coordinates domain operations, transaction boundaries, and event collection.
    All operations use the Unit of Work pattern for consistency.

    Example:
        with uow:
            result = service.create_checking(user_id, "My Checking", balance)
            if isinstance(result, Account):
                # Success
            else:
                # Handle AccountError

    Attributes:
        _uow: Unit of Work for transaction management.
    """

    def __init__(self, uow: "UnitOfWork") -> None:
        """Initialize AccountService with Unit of Work.

        Args:
            uow: Unit of Work for transaction management.
        """
        self._uow = uow

    # --- Create Operations ---

    async def create_checking(
        self,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        account_number: str | None = None,
        notes: str | None = None,
    ) -> Account | AccountError:
        """Create a new checking account.

        Args:
            user_id: Owner of the account.
            name: Display name for the account.
            opening_balance: Initial balance.
            institution: Optional bank/institution details.
            opening_date: Optional custom opening date (defaults to now).
            account_number: Optional account number (will be encrypted).
            notes: Optional notes.

        Returns:
            Created Account or AccountError on failure.
        """
        with self._uow:
            account = Account.create_checking(
                user_id=user_id,
                name=name,
                opening_balance=opening_balance,
                household_id=household_id,
                institution=institution,
                opening_date=opening_date,
                account_number=account_number,
                notes=notes,
            )
            self._uow.accounts.add(account)
            self._uow.collect_events(account.events)
            account.clear_events()
            await self._uow.commit()
            return account

    async def create_savings(
        self,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        account_number: str | None = None,
        notes: str | None = None,
    ) -> Account | AccountError:
        """Create a new savings account.

        Args:
            user_id: Owner of the account.
            name: Display name for the account.
            opening_balance: Initial balance.
            institution: Optional bank/institution details.
            opening_date: Optional custom opening date (defaults to now).
            account_number: Optional account number (will be encrypted).
            notes: Optional notes.

        Returns:
            Created Account or AccountError on failure.
        """
        with self._uow:
            account = Account.create_savings(
                user_id=user_id,
                name=name,
                opening_balance=opening_balance,
                household_id=household_id,
                institution=institution,
                opening_date=opening_date,
                account_number=account_number,
                notes=notes,
            )
            self._uow.accounts.add(account)
            self._uow.collect_events(account.events)
            account.clear_events()
            await self._uow.commit()
            return account

    async def create_credit_card(
        self,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        credit_limit: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Account | AccountError:
        """Create a new credit card account.

        Args:
            user_id: Owner of the account.
            name: Display name for the account.
            opening_balance: Initial balance (current balance owed).
            credit_limit: Credit limit for the card.
            institution: Optional bank/institution details.
            opening_date: Optional custom opening date (defaults to now).
            notes: Optional notes.

        Returns:
            Created Account or AccountError on failure.
        """
        try:
            with self._uow:
                account = Account.create_credit_card(
                    user_id=user_id,
                    name=name,
                    opening_balance=opening_balance,
                    credit_limit=credit_limit,
                    household_id=household_id,
                    institution=institution,
                    opening_date=opening_date,
                    notes=notes,
                )
                self._uow.accounts.add(account)
                self._uow.collect_events(account.events)
                account.clear_events()
                await self._uow.commit()
                return account
        except ValueError as e:
            return AccountError(code="VALIDATION_ERROR", message=str(e))

    async def create_loan(
        self,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        subtype: AccountSubtype | None = None,
        apr: Decimal | None = None,
        term_months: int | None = None,
        due_date: datetime | None = None,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Account | AccountError:
        """Create a new loan account.

        Args:
            user_id: Owner of the account.
            name: Display name for the account.
            opening_balance: Initial loan balance (amount owed).
            subtype: Optional loan subtype (auto, mortgage, student, personal).
            apr: Optional annual percentage rate (e.g., 0.0599 for 5.99%).
            term_months: Optional loan term in months.
            due_date: Optional due date for fixed-term loans.
            institution: Optional bank/institution details.
            opening_date: Optional custom opening date (defaults to now).
            notes: Optional notes.

        Returns:
            Created Account or AccountError on failure.
        """
        with self._uow:
            account = Account.create_loan(
                user_id=user_id,
                name=name,
                opening_balance=opening_balance,
                subtype=subtype,
                apr=apr,
                term_months=term_months,
                due_date=due_date,
                household_id=household_id,
                institution=institution,
                opening_date=opening_date,
                notes=notes,
            )
            self._uow.accounts.add(account)
            self._uow.collect_events(account.events)
            account.clear_events()
            await self._uow.commit()
            return account

    async def create_brokerage(
        self,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Account | AccountError:
        """Create a new brokerage account.

        Args:
            user_id: Owner of the account.
            name: Display name for the account.
            opening_balance: Initial balance.
            institution: Optional brokerage/institution details.
            opening_date: Optional custom opening date (defaults to now).
            notes: Optional notes.

        Returns:
            Created Account or AccountError on failure.
        """
        with self._uow:
            account = Account.create_brokerage(
                user_id=user_id,
                name=name,
                opening_balance=opening_balance,
                household_id=household_id,
                institution=institution,
                opening_date=opening_date,
                notes=notes,
            )
            self._uow.accounts.add(account)
            self._uow.collect_events(account.events)
            account.clear_events()
            await self._uow.commit()
            return account

    async def create_ira(
        self,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        subtype: AccountSubtype | None = None,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Account | AccountError:
        """Create a new IRA account.

        Args:
            user_id: Owner of the account.
            name: Display name for the account.
            opening_balance: Initial balance.
            subtype: Optional IRA subtype (traditional, Roth, SEP).
            institution: Optional brokerage/institution details.
            opening_date: Optional custom opening date (defaults to now).
            notes: Optional notes.

        Returns:
            Created Account or AccountError on failure.
        """
        try:
            with self._uow:
                account = Account.create_ira(
                    user_id=user_id,
                    name=name,
                    opening_balance=opening_balance,
                    subtype=subtype,
                    household_id=household_id,
                    institution=institution,
                    opening_date=opening_date,
                    notes=notes,
                )
                self._uow.accounts.add(account)
                self._uow.collect_events(account.events)
                account.clear_events()
                await self._uow.commit()
                return account
        except ValueError as e:
            return AccountError(code="VALIDATION_ERROR", message=str(e))

    async def create_rewards(
        self,
        user_id: UserId,
        name: str,
        rewards_balance: RewardsBalance,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Account | AccountError:
        """Create a new rewards account.

        Args:
            user_id: Owner of the account.
            name: Display name for the account.
            rewards_balance: Initial rewards balance (points/miles).
            institution: Optional airline/hotel/card issuer details.
            opening_date: Optional custom opening date (defaults to now).
            notes: Optional notes.

        Returns:
            Created Account or AccountError on failure.
        """
        with self._uow:
            account = Account.create_rewards(
                user_id=user_id,
                name=name,
                rewards_balance=rewards_balance,
                household_id=household_id,
                institution=institution,
                opening_date=opening_date,
                notes=notes,
            )
            self._uow.accounts.add(account)
            self._uow.collect_events(account.events)
            account.clear_events()
            await self._uow.commit()
            return account

    # --- Read Operations ---

    def get_account(
        self,
        account_id: AccountId,
        household_id: HouseholdId | None = None,
    ) -> Account | AccountError:
        """Get account by ID.

        If household_id is provided, verifies the account belongs to
        that household. Cross-household access returns NOT_FOUND (not FORBIDDEN)
        to prevent information leaking.

        Args:
            account_id: The account identifier.
            household_id: Optional household for ownership verification.

        Returns:
            The Account or AccountError if not found.
        """
        with self._uow:
            account = self._uow.accounts.get(account_id)
            if account is None:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            # Cross-household access returns 404 (security: prevents probing)
            if household_id is not None and account.household_id != household_id:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            return account

    def get_household_accounts(
        self,
        household_id: HouseholdId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a household with optional filters.

        Args:
            household_id: The household identifier for data scoping.
            status: Optional status filter (ACTIVE, CLOSED).
            account_type: Optional account type filter.

        Returns:
            List of matching accounts, sorted by sort_order then name.
        """
        with self._uow:
            return self._uow.accounts.get_by_household(
                household_id=household_id,
                status=status,
                account_type=account_type,
            )

    def get_user_accounts(
        self,
        user_id: UserId,
        status: AccountStatus | None = None,
        account_type: AccountType | None = None,
    ) -> list[Account]:
        """Get all accounts for a user with optional filters.

        Args:
            user_id: The user identifier.
            status: Optional status filter (ACTIVE, CLOSED).
            account_type: Optional account type filter.

        Returns:
            List of matching accounts, sorted by sort_order then name.
        """
        with self._uow:
            return self._uow.accounts.get_by_user(
                user_id=user_id,
                status=status,
                account_type=account_type,
            )

    # --- Lifecycle Operations ---

    async def close_account(
        self,
        account_id: AccountId,
        closed_by: UserId | None = None,
        household_id: HouseholdId | None = None,
    ) -> Account | AccountError:
        """Close an account.

        Args:
            account_id: The account to close.
            closed_by: Optional user who performed the close.
            household_id: Optional household for ownership verification.

        Returns:
            The closed Account or AccountError on failure.
        """
        with self._uow:
            account = self._uow.accounts.get(account_id)
            if account is None:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            if household_id is not None and account.household_id != household_id:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            try:
                account.close(closed_by)
                self._uow.collect_events(account.events)
                account.clear_events()
                await self._uow.commit()
                return account
            except ValueError as e:
                return AccountError(code="ALREADY_CLOSED", message=str(e))

    async def reopen_account(
        self,
        account_id: AccountId,
        reopened_by: UserId | None = None,
        household_id: HouseholdId | None = None,
    ) -> Account | AccountError:
        """Reopen a closed account.

        Args:
            account_id: The account to reopen.
            reopened_by: Optional user who performed the reopen.
            household_id: Optional household for ownership verification.

        Returns:
            The reopened Account or AccountError on failure.
        """
        with self._uow:
            account = self._uow.accounts.get(account_id)
            if account is None:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            if household_id is not None and account.household_id != household_id:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            try:
                account.reopen(reopened_by)
                self._uow.collect_events(account.events)
                account.clear_events()
                await self._uow.commit()
                return account
            except ValueError as e:
                return AccountError(code="NOT_CLOSED", message=str(e))

    async def delete_account(
        self,
        account_id: AccountId,
        household_id: HouseholdId | None = None,
    ) -> bool | AccountError:
        """Delete an account without transactions.

        Accounts with transactions cannot be deleted - they should be closed.

        Args:
            account_id: The account to delete.
            household_id: Optional household for ownership verification.

        Returns:
            True on success, AccountError on failure.
        """
        with self._uow:
            account = self._uow.accounts.get(account_id)
            if account is None:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            if household_id is not None and account.household_id != household_id:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )

            if self._uow.accounts.has_transactions(account_id):
                return AccountError(
                    code="HAS_TRANSACTIONS",
                    message="Cannot delete account with transactions. Close it instead.",
                )

            # Emit delete event before actual deletion
            delete_event = AccountDeleted(
                aggregate_id=str(account.id),
                aggregate_type="Account",
            )
            self._uow.collect_events([delete_event])
            self._uow.accounts.delete(account)
            await self._uow.commit()
            return True

    # --- Update Operations ---

    async def update_account_name(
        self,
        account_id: AccountId,
        new_name: str,
        updated_by: UserId | None = None,
        household_id: HouseholdId | None = None,
    ) -> Account | AccountError:
        """Update account name.

        Args:
            account_id: The account to update.
            new_name: The new name for the account.
            updated_by: Optional user who performed the update.

        Returns:
            The updated Account or AccountError on failure.
        """
        with self._uow:
            account = self._uow.accounts.get(account_id)
            if account is None:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            if household_id is not None and account.household_id != household_id:
                return AccountError(
                    code="NOT_FOUND",
                    message=f"Account {account_id} not found",
                )
            try:
                account.update_name(new_name, updated_by)
                self._uow.collect_events(account.events)
                account.clear_events()
                await self._uow.commit()
                return account
            except ValueError as e:
                return AccountError(code="VALIDATION_ERROR", message=str(e))
