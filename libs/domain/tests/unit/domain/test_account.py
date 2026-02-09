"""Unit tests for Account aggregate root.

Tests cover:
- Factory methods for all 7 account types
- Event emission on state changes
- Lifecycle operations (close/reopen)
- Property update methods
- Properties (is_active, available_credit)
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from domain.events.account_events import (
    AccountClosed,
    AccountCreated,
    AccountReopened,
    AccountUpdated,
)
from domain.model.account import Account
from domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from domain.model.entity_id import UserId
from domain.model.institution import InstitutionDetails
from domain.model.money import Money
from domain.model.rewards_balance import RewardsBalance

# --- Fixtures ---


@pytest.fixture
def user_id() -> UserId:
    """Generate test UserId."""
    return UserId.generate()


@pytest.fixture
def usd_balance() -> Money:
    """Standard USD balance for testing."""
    return Money(Decimal("1000"), "USD")


@pytest.fixture
def sample_institution() -> InstitutionDetails:
    """Sample institution for testing."""
    return InstitutionDetails(name="Test Bank")


# --- Factory Method Tests ---


class TestAccountFactoryMethods:
    """Tests for Account factory methods."""

    def test_create_checking_account(self, user_id: UserId, usd_balance: Money):
        """Creates checking account with correct type, generates ID, emits event."""
        account = Account.create_checking(
            user_id=user_id,
            name="My Checking",
            opening_balance=usd_balance,
        )

        assert account.account_type == AccountType.CHECKING
        assert account.status == AccountStatus.ACTIVE
        assert account.name == "My Checking"
        assert account.opening_balance == usd_balance
        assert account.id is not None
        assert str(account.id).startswith("acct_")

        # Event emitted
        assert len(account.events) == 1
        event = account.events[0]
        assert isinstance(event, AccountCreated)
        assert event.account_name == "My Checking"
        assert event.account_type == "checking"

    def test_create_savings_account(self, user_id: UserId, usd_balance: Money):
        """Creates savings account with correct type."""
        account = Account.create_savings(
            user_id=user_id,
            name="My Savings",
            opening_balance=usd_balance,
        )

        assert account.account_type == AccountType.SAVINGS
        assert account.status == AccountStatus.ACTIVE
        assert account.name == "My Savings"

    def test_create_credit_card_account(self, user_id: UserId):
        """Creates credit card with required credit_limit."""
        opening_balance = Money(Decimal("500"), "USD")
        credit_limit = Money(Decimal("5000"), "USD")

        account = Account.create_credit_card(
            user_id=user_id,
            name="My Credit Card",
            opening_balance=opening_balance,
            credit_limit=credit_limit,
        )

        assert account.account_type == AccountType.CREDIT_CARD
        assert account.credit_limit == credit_limit
        assert account.status == AccountStatus.ACTIVE

    def test_create_credit_card_currency_mismatch(self, user_id: UserId):
        """Raises ValueError when credit_limit currency differs from balance."""
        usd_balance = Money(Decimal("500"), "USD")
        eur_limit = Money(Decimal("5000"), "EUR")

        with pytest.raises(ValueError, match="currency must match"):
            Account.create_credit_card(
                user_id=user_id,
                name="Card",
                opening_balance=usd_balance,
                credit_limit=eur_limit,
            )

    def test_create_loan_account(self, user_id: UserId, usd_balance: Money):
        """Creates loan account with APR, term_months, due_date, subtype."""
        due = datetime(2030, 1, 15, tzinfo=UTC)

        account = Account.create_loan(
            user_id=user_id,
            name="Car Loan",
            opening_balance=usd_balance,
            subtype=AccountSubtype.AUTO_LOAN,
            apr=Decimal("0.0599"),
            term_months=60,
            due_date=due,
        )

        assert account.account_type == AccountType.LOAN
        assert account.subtype == AccountSubtype.AUTO_LOAN
        assert account.apr == Decimal("0.0599")
        assert account.term_months == 60
        assert account.due_date == due

    def test_create_brokerage_account(self, user_id: UserId, usd_balance: Money):
        """Creates brokerage account with correct type."""
        account = Account.create_brokerage(
            user_id=user_id,
            name="Brokerage",
            opening_balance=usd_balance,
        )

        assert account.account_type == AccountType.BROKERAGE
        assert account.status == AccountStatus.ACTIVE

    def test_create_ira_account(self, user_id: UserId, usd_balance: Money):
        """Creates IRA account with IRA subtype."""
        account = Account.create_ira(
            user_id=user_id,
            name="Roth IRA",
            opening_balance=usd_balance,
            subtype=AccountSubtype.ROTH_IRA,
        )

        assert account.account_type == AccountType.IRA
        assert account.subtype == AccountSubtype.ROTH_IRA

    def test_create_ira_invalid_subtype(self, user_id: UserId, usd_balance: Money):
        """Raises ValueError for non-IRA subtype on IRA account."""
        with pytest.raises(ValueError, match="Invalid IRA subtype"):
            Account.create_ira(
                user_id=user_id,
                name="IRA",
                opening_balance=usd_balance,
                subtype=AccountSubtype.AUTO_LOAN,  # Not an IRA subtype
            )

    def test_create_rewards_account(self, user_id: UserId):
        """Creates rewards account with RewardsBalance instead of Money."""
        rewards = RewardsBalance(Decimal("50000"), "Alaska Miles")

        account = Account.create_rewards(
            user_id=user_id,
            name="Alaska Miles",
            rewards_balance=rewards,
        )

        assert account.account_type == AccountType.REWARDS
        assert account.rewards_balance == rewards
        # opening_balance is zero Money for rewards accounts
        assert account.opening_balance.amount == Decimal("0")


# --- Event Emission Tests ---


class TestAccountEventEmission:
    """Tests for Account event emission."""

    def test_account_created_event_emitted(self, user_id: UserId, usd_balance: Money):
        """Factory methods emit AccountCreated event."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        assert len(account.events) == 1
        event = account.events[0]
        assert isinstance(event, AccountCreated)
        assert event.aggregate_id == str(account.id)
        assert event.aggregate_type == "Account"
        assert event.account_name == "Checking"

    def test_account_updated_event_emitted(self, user_id: UserId, usd_balance: Money):
        """update_name emits AccountUpdated with old/new values."""
        account = Account.create_checking(
            user_id=user_id,
            name="Old Name",
            opening_balance=usd_balance,
        )
        account.clear_events()

        account.update_name("New Name")

        assert len(account.events) == 1
        event = account.events[0]
        assert isinstance(event, AccountUpdated)
        assert event.field == "name"
        assert event.old_value == "Old Name"
        assert event.new_value == "New Name"

    def test_account_closed_event_emitted(self, user_id: UserId, usd_balance: Money):
        """close() emits AccountClosed event."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )
        account.clear_events()

        account.close()

        assert len(account.events) == 1
        event = account.events[0]
        assert isinstance(event, AccountClosed)
        assert event.aggregate_id == str(account.id)

    def test_account_reopened_event_emitted(self, user_id: UserId, usd_balance: Money):
        """reopen() emits AccountReopened event."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )
        account.close()
        account.clear_events()

        account.reopen()

        assert len(account.events) == 1
        event = account.events[0]
        assert isinstance(event, AccountReopened)
        assert event.aggregate_id == str(account.id)

    def test_clear_events(self, user_id: UserId, usd_balance: Money):
        """clear_events() empties the events list."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        assert len(account.events) == 1
        account.clear_events()
        assert len(account.events) == 0


# --- Lifecycle Tests ---


class TestAccountLifecycle:
    """Tests for Account lifecycle operations."""

    def test_close_active_account(self, user_id: UserId, usd_balance: Money):
        """Sets status=CLOSED, sets closing_date."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        account.close()

        assert account.status == AccountStatus.CLOSED
        assert account.closing_date is not None

    def test_close_already_closed_account(self, user_id: UserId, usd_balance: Money):
        """Raises ValueError when closing already closed account."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )
        account.close()

        with pytest.raises(ValueError, match="already closed"):
            account.close()

    def test_reopen_closed_account(self, user_id: UserId, usd_balance: Money):
        """Sets status=ACTIVE, clears closing_date."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )
        account.close()

        account.reopen()

        assert account.status == AccountStatus.ACTIVE
        assert account.closing_date is None

    def test_reopen_active_account(self, user_id: UserId, usd_balance: Money):
        """Raises ValueError when reopening non-closed account."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        with pytest.raises(ValueError, match="closed accounts can be reopened"):
            account.reopen()


# --- Property Update Tests ---


class TestAccountPropertyUpdates:
    """Tests for Account property update methods."""

    def test_update_name(self, user_id: UserId, usd_balance: Money):
        """Updates name, sets updated_at."""
        account = Account.create_checking(
            user_id=user_id,
            name="Old Name",
            opening_balance=usd_balance,
        )
        original_updated_at = account.updated_at

        account.update_name("New Name")

        assert account.name == "New Name"
        assert account.updated_at >= original_updated_at

    def test_update_name_empty(self, user_id: UserId, usd_balance: Money):
        """Raises ValueError for empty/whitespace name."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        with pytest.raises(ValueError, match=r"(?i)name cannot be empty"):
            account.update_name("")

        with pytest.raises(ValueError, match=r"(?i)name cannot be empty"):
            account.update_name("   ")

    def test_update_notes(self, user_id: UserId, usd_balance: Money):
        """Updates notes field."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        account.update_notes("Some notes")

        assert account.notes == "Some notes"

    def test_update_notes_to_none(self, user_id: UserId, usd_balance: Money):
        """Can set notes to None."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
            notes="Initial notes",
        )

        account.update_notes(None)

        assert account.notes is None

    def test_update_institution(
        self,
        user_id: UserId,
        usd_balance: Money,
        sample_institution: InstitutionDetails,
    ):
        """Updates institution."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        account.update_institution(sample_institution)

        assert account.institution == sample_institution


# --- Property Tests ---


class TestAccountProperties:
    """Tests for Account properties."""

    def test_is_active_property(self, user_id: UserId, usd_balance: Money):
        """Returns True for ACTIVE, False for CLOSED."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        assert account.is_active is True

        account.close()
        assert account.is_active is False

    def test_available_credit_for_credit_card(self, user_id: UserId):
        """Returns credit_limit for credit cards (placeholder)."""
        credit_limit = Money(Decimal("5000"), "USD")
        account = Account.create_credit_card(
            user_id=user_id,
            name="Credit Card",
            opening_balance=Money(Decimal("0"), "USD"),
            credit_limit=credit_limit,
        )

        assert account.available_credit == credit_limit

    def test_available_credit_for_non_credit_card(
        self, user_id: UserId, usd_balance: Money
    ):
        """Returns None for non-credit card accounts."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )

        assert account.available_credit is None


# --- Additional Tests ---


class TestAccountWithInstitution:
    """Tests for Account with institution details."""

    def test_create_with_institution(
        self,
        user_id: UserId,
        usd_balance: Money,
        sample_institution: InstitutionDetails,
    ):
        """Can create account with institution."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
            institution=sample_institution,
        )

        assert account.institution == sample_institution
        assert account.institution is not None
        assert account.institution.name == "Test Bank"

    def test_create_with_account_number(self, user_id: UserId, usd_balance: Money):
        """Can create account with account number."""
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
            account_number="123456789",
        )

        assert account.encrypted_account_number == "123456789"


class TestAccountWithOpeningDate:
    """Tests for Account opening date handling."""

    def test_default_opening_date(self, user_id: UserId, usd_balance: Money):
        """Opening date defaults to now if not provided."""
        before = datetime.now(UTC)
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )
        after = datetime.now(UTC)

        assert before <= account.opening_date <= after

    def test_custom_opening_date(self, user_id: UserId, usd_balance: Money):
        """Can specify custom opening date."""
        custom_date = datetime(2020, 1, 1, tzinfo=UTC)
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
            opening_date=custom_date,
        )

        assert account.opening_date == custom_date
