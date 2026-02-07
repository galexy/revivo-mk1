"""Account aggregate root entity.

The Account aggregate is the core domain entity for financial account management.
It supports multiple account types (checking, savings, credit card, loan, brokerage,
IRA, rewards) with type-specific validation and behavior.

Key design decisions:
- Single class with type discriminator (not subclasses per type)
- Factory methods for type-specific validation
- Not frozen - uses explicit mutation methods that emit events
- eq=False because identity is based on ID, not field values
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Self

from domain.events.account_events import (
    AccountClosed,
    AccountCreated,
    AccountReopened,
    AccountUpdated,
)
from domain.events.base import DomainEvent
from domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from domain.model.entity_id import AccountId, HouseholdId, UserId
from domain.model.institution import InstitutionDetails
from domain.model.money import Money
from domain.model.rewards_balance import RewardsBalance


@dataclass(eq=False)
class Account:
    """Account aggregate root.

    Supports multiple account types with type-specific fields.
    Uses factory methods for type-specific validation.
    Not frozen - uses explicit mutation methods that emit events.

    Note: Does not use slots=True because SQLAlchemy imperative mapping
    requires __dict__ and __weakref__ for instance state tracking.
    """

    # Identity
    id: AccountId
    user_id: UserId
    household_id: HouseholdId
    name: str
    account_type: AccountType
    status: AccountStatus

    # Opening/balance info
    opening_balance: Money
    opening_date: datetime

    # Optional type-specific fields
    subtype: AccountSubtype | None = None
    credit_limit: Money | None = None  # Credit cards only
    apr: Decimal | None = None  # Loans only (e.g., 0.1999 for 19.99%)
    term_months: int | None = None  # Loans only
    due_date: datetime | None = None  # Loans with fixed terms
    rewards_balance: RewardsBalance | None = None  # Rewards accounts

    # Institution metadata
    institution: InstitutionDetails | None = None
    encrypted_account_number: str | None = None

    # Lifecycle
    closing_date: datetime | None = None
    notes: str | None = None
    sort_order: int = 0

    # Audit
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: UserId | None = None
    updated_by: UserId | None = None

    # Domain events (not persisted directly)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @property
    def events(self) -> list[DomainEvent]:
        """Get collected domain events as a copy."""
        return list(self._events)

    def clear_events(self) -> None:
        """Clear collected events after processing."""
        self._events.clear()

    @property
    def is_active(self) -> bool:
        """Check if account is active."""
        return self.status == AccountStatus.ACTIVE

    @property
    def available_credit(self) -> Money | None:
        """Calculate available credit for credit cards.

        Note: In Phase 3, this will be calculated as:
        credit_limit - current_balance (from transactions)

        For now, returns credit_limit as a placeholder.
        """
        if self.account_type != AccountType.CREDIT_CARD or self.credit_limit is None:
            return None
        return self.credit_limit

    # --- Factory Methods ---

    @classmethod
    def create_checking(
        cls,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        account_number: str | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for checking account."""
        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            account_type=AccountType.CHECKING,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            institution=institution,
            encrypted_account_number=account_number,  # Will be encrypted by adapter
            notes=notes,
        )
        account._events.append(
            AccountCreated(
                aggregate_id=str(account.id),
                aggregate_type="Account",
                account_name=name,
                account_type=AccountType.CHECKING.value,
            )
        )
        return account

    @classmethod
    def create_savings(
        cls,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        account_number: str | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for savings account."""
        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            account_type=AccountType.SAVINGS,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            institution=institution,
            encrypted_account_number=account_number,
            notes=notes,
        )
        account._events.append(
            AccountCreated(
                aggregate_id=str(account.id),
                aggregate_type="Account",
                account_name=name,
                account_type=AccountType.SAVINGS.value,
            )
        )
        return account

    @classmethod
    def create_credit_card(
        cls,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        credit_limit: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for credit card account with required credit_limit."""
        if credit_limit.currency != opening_balance.currency:
            raise ValueError("Credit limit currency must match balance currency")

        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            account_type=AccountType.CREDIT_CARD,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            credit_limit=credit_limit,
            institution=institution,
            notes=notes,
        )
        account._events.append(
            AccountCreated(
                aggregate_id=str(account.id),
                aggregate_type="Account",
                account_name=name,
                account_type=AccountType.CREDIT_CARD.value,
            )
        )
        return account

    @classmethod
    def create_loan(
        cls,
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
    ) -> Self:
        """Factory for loan account with optional APR, term, and due_date."""
        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            account_type=AccountType.LOAN,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            subtype=subtype,
            apr=apr,
            term_months=term_months,
            due_date=due_date,
            institution=institution,
            notes=notes,
        )
        account._events.append(
            AccountCreated(
                aggregate_id=str(account.id),
                aggregate_type="Account",
                account_name=name,
                account_type=AccountType.LOAN.value,
            )
        )
        return account

    @classmethod
    def create_brokerage(
        cls,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for brokerage account."""
        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            account_type=AccountType.BROKERAGE,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            institution=institution,
            notes=notes,
        )
        account._events.append(
            AccountCreated(
                aggregate_id=str(account.id),
                aggregate_type="Account",
                account_name=name,
                account_type=AccountType.BROKERAGE.value,
            )
        )
        return account

    @classmethod
    def create_ira(
        cls,
        user_id: UserId,
        name: str,
        opening_balance: Money,
        subtype: AccountSubtype | None = None,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for IRA account with optional IRA-specific subtype."""
        # Validate subtype is IRA-related if provided
        ira_subtypes = {
            AccountSubtype.TRADITIONAL_IRA,
            AccountSubtype.ROTH_IRA,
            AccountSubtype.SEP_IRA,
        }
        if subtype is not None and subtype not in ira_subtypes:
            raise ValueError(
                f"Invalid IRA subtype: {subtype}. "
                f"Must be one of: {', '.join(s.value for s in ira_subtypes)}"
            )

        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            account_type=AccountType.IRA,
            status=AccountStatus.ACTIVE,
            opening_balance=opening_balance,
            opening_date=opening_date or datetime.now(UTC),
            subtype=subtype,
            institution=institution,
            notes=notes,
        )
        account._events.append(
            AccountCreated(
                aggregate_id=str(account.id),
                aggregate_type="Account",
                account_name=name,
                account_type=AccountType.IRA.value,
            )
        )
        return account

    @classmethod
    def create_rewards(
        cls,
        user_id: UserId,
        name: str,
        rewards_balance: RewardsBalance,
        household_id: HouseholdId | None = None,
        institution: InstitutionDetails | None = None,
        opening_date: datetime | None = None,
        notes: str | None = None,
    ) -> Self:
        """Factory for rewards account using RewardsBalance instead of Money."""
        # Create with zero Money balance since rewards use RewardsBalance
        zero_balance = Money(Decimal("0"), "USD")

        account = cls(
            id=AccountId.generate(),
            user_id=user_id,
            household_id=household_id
            or HouseholdId.from_string("hh_00000000000000000000000000"),
            name=name,
            account_type=AccountType.REWARDS,
            status=AccountStatus.ACTIVE,
            opening_balance=zero_balance,
            opening_date=opening_date or datetime.now(UTC),
            rewards_balance=rewards_balance,
            institution=institution,
            notes=notes,
        )
        account._events.append(
            AccountCreated(
                aggregate_id=str(account.id),
                aggregate_type="Account",
                account_name=name,
                account_type=AccountType.REWARDS.value,
            )
        )
        return account

    # --- Lifecycle Methods ---

    def close(self, closed_by: UserId | None = None) -> None:
        """Close the account."""
        if self.status == AccountStatus.CLOSED:
            raise ValueError("Account is already closed")

        self.status = AccountStatus.CLOSED
        self.closing_date = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.updated_by = closed_by

        self._events.append(
            AccountClosed(
                aggregate_id=str(self.id),
                aggregate_type="Account",
            )
        )

    def reopen(self, reopened_by: UserId | None = None) -> None:
        """Reopen a closed account."""
        if self.status != AccountStatus.CLOSED:
            raise ValueError("Only closed accounts can be reopened")

        self.status = AccountStatus.ACTIVE
        self.closing_date = None
        self.updated_at = datetime.now(UTC)
        self.updated_by = reopened_by

        self._events.append(
            AccountReopened(
                aggregate_id=str(self.id),
                aggregate_type="Account",
            )
        )

    # --- Property Update Methods ---

    def update_name(self, new_name: str, updated_by: UserId | None = None) -> None:
        """Update account name."""
        if not new_name or not new_name.strip():
            raise ValueError("Account name cannot be empty")

        old_name = self.name
        self.name = new_name.strip()
        self.updated_at = datetime.now(UTC)
        self.updated_by = updated_by

        self._events.append(
            AccountUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Account",
                field="name",
                old_value=old_name,
                new_value=self.name,
            )
        )

    def update_notes(self, notes: str | None, updated_by: UserId | None = None) -> None:
        """Update account notes."""
        old_notes = self.notes
        self.notes = notes
        self.updated_at = datetime.now(UTC)
        self.updated_by = updated_by

        self._events.append(
            AccountUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Account",
                field="notes",
                old_value=old_notes,
                new_value=notes,
            )
        )

    def update_institution(
        self, institution: InstitutionDetails | None, updated_by: UserId | None = None
    ) -> None:
        """Update account institution."""
        old_institution_name = self.institution.name if self.institution else None
        new_institution_name = institution.name if institution else None

        self.institution = institution
        self.updated_at = datetime.now(UTC)
        self.updated_by = updated_by

        self._events.append(
            AccountUpdated(
                aggregate_id=str(self.id),
                aggregate_type="Account",
                field="institution",
                old_value=old_institution_name,
                new_value=new_institution_name,
            )
        )
