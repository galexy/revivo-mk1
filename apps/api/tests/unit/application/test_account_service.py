"""Unit tests for AccountService application service.

Tests cover:
- Account creation for all 7 account types
- Account retrieval (found and not found)
- Lifecycle operations (close, reopen)
- Delete operations (with and without transactions)
- Update operations (name)
- Event collection before commit

All tests use mock UnitOfWork to isolate service behavior.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from domain.events.account_events import (
    AccountClosed,
    AccountCreated,
    AccountDeleted,
    AccountReopened,
    AccountUpdated,
)
from domain.model.account import Account
from domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from domain.model.entity_id import AccountId, UserId
from domain.model.institution import InstitutionDetails
from domain.model.money import Money
from domain.model.rewards_balance import RewardsBalance
from src.application.services.account_service import AccountError, AccountService

# --- Fixtures ---


@pytest.fixture
def mock_uow():
    """Create mock Unit of Work with mock repository."""
    uow = MagicMock()
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    # Mock accounts repository
    accounts_repo = MagicMock()
    type(uow).accounts = PropertyMock(return_value=accounts_repo)

    # Store collected events for verification
    uow._collected_events = []

    def collect_events(events):
        uow._collected_events.extend(events)

    uow.collect_events = MagicMock(side_effect=collect_events)

    # commit() is now async, must be AsyncMock
    uow.commit = AsyncMock()

    return uow


@pytest.fixture
def service(mock_uow):
    """Create AccountService with mock UoW."""
    return AccountService(mock_uow)


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


# --- Account Creation Tests ---


class TestAccountCreation:
    """Tests for account creation methods."""

    def test_create_checking_account(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Creates checking account, adds to repo, collects events, commits."""
        result = asyncio.run(
            service.create_checking(
                user_id=user_id,
                name="My Checking",
                opening_balance=usd_balance,
            )
        )

        assert isinstance(result, Account)
        assert result.account_type == AccountType.CHECKING
        assert result.name == "My Checking"
        assert result.user_id == user_id
        assert result.opening_balance == usd_balance

        # Verify UoW interactions
        mock_uow.accounts.add.assert_called_once_with(result)
        mock_uow.collect_events.assert_called_once()
        mock_uow.commit.assert_called_once()

        # Verify event was collected
        assert len(mock_uow._collected_events) == 1
        event = mock_uow._collected_events[0]
        assert isinstance(event, AccountCreated)
        assert event.account_type == "checking"

    def test_create_savings_account(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Creates savings account with correct type."""
        result = asyncio.run(
            service.create_savings(
                user_id=user_id,
                name="Emergency Fund",
                opening_balance=usd_balance,
            )
        )

        assert isinstance(result, Account)
        assert result.account_type == AccountType.SAVINGS
        mock_uow.accounts.add.assert_called_once()
        mock_uow.commit.assert_called_once()

    def test_create_credit_card_account(
        self, service: AccountService, mock_uow, user_id: UserId
    ):
        """Creates credit card with credit_limit."""
        balance = Money(Decimal("500"), "USD")
        limit = Money(Decimal("5000"), "USD")

        result = asyncio.run(
            service.create_credit_card(
                user_id=user_id,
                name="Visa Rewards",
                opening_balance=balance,
                credit_limit=limit,
            )
        )

        assert isinstance(result, Account)
        assert result.account_type == AccountType.CREDIT_CARD
        assert result.credit_limit == limit
        mock_uow.commit.assert_called_once()

    def test_create_credit_card_currency_mismatch(
        self, service: AccountService, mock_uow, user_id: UserId
    ):
        """Returns AccountError when credit_limit currency differs from balance."""
        usd_balance = Money(Decimal("500"), "USD")
        eur_limit = Money(Decimal("5000"), "EUR")

        result = asyncio.run(
            service.create_credit_card(
                user_id=user_id,
                name="Card",
                opening_balance=usd_balance,
                credit_limit=eur_limit,
            )
        )

        assert isinstance(result, AccountError)
        assert result.code == "VALIDATION_ERROR"
        assert "currency" in result.message.lower()
        mock_uow.commit.assert_not_called()

    def test_create_loan_account(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Creates loan with APR, term_months, subtype."""
        result = asyncio.run(
            service.create_loan(
                user_id=user_id,
                name="Car Loan",
                opening_balance=usd_balance,
                subtype=AccountSubtype.AUTO_LOAN,
                apr=Decimal("0.0599"),
                term_months=60,
            )
        )

        assert isinstance(result, Account)
        assert result.account_type == AccountType.LOAN
        assert result.subtype == AccountSubtype.AUTO_LOAN
        assert result.apr == Decimal("0.0599")
        assert result.term_months == 60
        mock_uow.commit.assert_called_once()

    def test_create_brokerage_account(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Creates brokerage account."""
        result = asyncio.run(
            service.create_brokerage(
                user_id=user_id,
                name="Fidelity",
                opening_balance=usd_balance,
            )
        )

        assert isinstance(result, Account)
        assert result.account_type == AccountType.BROKERAGE
        mock_uow.commit.assert_called_once()

    def test_create_ira_account(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Creates IRA with IRA subtype."""
        result = asyncio.run(
            service.create_ira(
                user_id=user_id,
                name="Roth IRA",
                opening_balance=usd_balance,
                subtype=AccountSubtype.ROTH_IRA,
            )
        )

        assert isinstance(result, Account)
        assert result.account_type == AccountType.IRA
        assert result.subtype == AccountSubtype.ROTH_IRA
        mock_uow.commit.assert_called_once()

    def test_create_ira_invalid_subtype(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns AccountError for non-IRA subtype."""
        result = asyncio.run(
            service.create_ira(
                user_id=user_id,
                name="IRA",
                opening_balance=usd_balance,
                subtype=AccountSubtype.AUTO_LOAN,
            )
        )

        assert isinstance(result, AccountError)
        assert result.code == "VALIDATION_ERROR"
        assert "IRA subtype" in result.message
        mock_uow.commit.assert_not_called()

    def test_create_rewards_account(
        self, service: AccountService, mock_uow, user_id: UserId
    ):
        """Creates rewards account with RewardsBalance."""
        rewards = RewardsBalance(Decimal("50000"), "Alaska Miles")

        result = asyncio.run(
            service.create_rewards(
                user_id=user_id,
                name="Alaska Miles",
                rewards_balance=rewards,
            )
        )

        assert isinstance(result, Account)
        assert result.account_type == AccountType.REWARDS
        assert result.rewards_balance == rewards
        mock_uow.commit.assert_called_once()


# --- Account Retrieval Tests ---


class TestAccountRetrieval:
    """Tests for account retrieval methods."""

    def test_get_account_found(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns account when found."""
        account_id = AccountId.generate()
        account = Account.create_checking(
            user_id=user_id,
            name="Checking",
            opening_balance=usd_balance,
        )
        # Override the generated ID for testing
        object.__setattr__(account, "id", account_id)
        mock_uow.accounts.get.return_value = account

        result = service.get_account(account_id)

        assert isinstance(result, Account)
        assert result.name == "Checking"
        mock_uow.accounts.get.assert_called_once_with(account_id)

    def test_get_account_not_found(self, service: AccountService, mock_uow):
        """Returns AccountError when account not found."""
        account_id = AccountId.generate()
        mock_uow.accounts.get.return_value = None

        result = service.get_account(account_id)

        assert isinstance(result, AccountError)
        assert result.code == "NOT_FOUND"
        assert str(account_id) in result.message

    def test_get_user_accounts(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns list of accounts for user."""
        accounts = [
            Account.create_checking(
                user_id=user_id, name="Checking", opening_balance=usd_balance
            ),
            Account.create_savings(
                user_id=user_id, name="Savings", opening_balance=usd_balance
            ),
        ]
        mock_uow.accounts.get_by_user.return_value = accounts

        result = service.get_user_accounts(user_id)

        assert len(result) == 2
        mock_uow.accounts.get_by_user.assert_called_once_with(
            user_id=user_id, status=None, account_type=None
        )

    def test_get_user_accounts_with_filters(
        self, service: AccountService, mock_uow, user_id: UserId
    ):
        """Passes filters to repository."""
        mock_uow.accounts.get_by_user.return_value = []

        service.get_user_accounts(
            user_id,
            status=AccountStatus.ACTIVE,
            account_type=AccountType.CHECKING,
        )

        mock_uow.accounts.get_by_user.assert_called_once_with(
            user_id=user_id,
            status=AccountStatus.ACTIVE,
            account_type=AccountType.CHECKING,
        )


# --- Lifecycle Operation Tests ---


class TestLifecycleOperations:
    """Tests for close and reopen operations."""

    def test_close_account_success(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Closes account, collects event, commits."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        account.clear_events()
        mock_uow.accounts.get.return_value = account

        result = asyncio.run(service.close_account(account.id))

        assert isinstance(result, Account)
        assert result.status == AccountStatus.CLOSED
        assert result.closing_date is not None
        mock_uow.collect_events.assert_called_once()
        mock_uow.commit.assert_called_once()

        # Verify AccountClosed event was collected
        assert len(mock_uow._collected_events) == 1
        event = mock_uow._collected_events[0]
        assert isinstance(event, AccountClosed)

    def test_close_account_not_found(self, service: AccountService, mock_uow):
        """Returns AccountError when account not found."""
        account_id = AccountId.generate()
        mock_uow.accounts.get.return_value = None

        result = asyncio.run(service.close_account(account_id))

        assert isinstance(result, AccountError)
        assert result.code == "NOT_FOUND"
        mock_uow.commit.assert_not_called()

    def test_close_already_closed_account(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns AccountError when closing already closed account."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        account.close()
        account.clear_events()
        mock_uow.accounts.get.return_value = account

        result = asyncio.run(service.close_account(account.id))

        assert isinstance(result, AccountError)
        assert result.code == "ALREADY_CLOSED"
        mock_uow.commit.assert_not_called()

    def test_reopen_account_success(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Reopens closed account, collects event, commits."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        account.close()
        account.clear_events()
        mock_uow.accounts.get.return_value = account

        result = asyncio.run(service.reopen_account(account.id))

        assert isinstance(result, Account)
        assert result.status == AccountStatus.ACTIVE
        assert result.closing_date is None
        mock_uow.collect_events.assert_called_once()
        mock_uow.commit.assert_called_once()

        # Verify AccountReopened event was collected
        assert len(mock_uow._collected_events) == 1
        event = mock_uow._collected_events[0]
        assert isinstance(event, AccountReopened)

    def test_reopen_account_not_found(self, service: AccountService, mock_uow):
        """Returns AccountError when account not found."""
        account_id = AccountId.generate()
        mock_uow.accounts.get.return_value = None

        result = asyncio.run(service.reopen_account(account_id))

        assert isinstance(result, AccountError)
        assert result.code == "NOT_FOUND"
        mock_uow.commit.assert_not_called()

    def test_reopen_active_account(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns AccountError when reopening active account."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        account.clear_events()
        mock_uow.accounts.get.return_value = account

        result = asyncio.run(service.reopen_account(account.id))

        assert isinstance(result, AccountError)
        assert result.code == "NOT_CLOSED"
        mock_uow.commit.assert_not_called()


# --- Delete Operation Tests ---


class TestDeleteOperations:
    """Tests for delete operation."""

    def test_delete_account_success(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Deletes account without transactions, collects event, commits."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        mock_uow.accounts.get.return_value = account
        mock_uow.accounts.has_transactions.return_value = False

        result = asyncio.run(service.delete_account(account.id))

        assert result is True
        mock_uow.accounts.delete.assert_called_once_with(account)
        mock_uow.collect_events.assert_called_once()
        mock_uow.commit.assert_called_once()

        # Verify AccountDeleted event was collected
        assert len(mock_uow._collected_events) == 1
        event = mock_uow._collected_events[0]
        assert isinstance(event, AccountDeleted)

    def test_delete_account_not_found(self, service: AccountService, mock_uow):
        """Returns AccountError when account not found."""
        account_id = AccountId.generate()
        mock_uow.accounts.get.return_value = None

        result = asyncio.run(service.delete_account(account_id))

        assert isinstance(result, AccountError)
        assert result.code == "NOT_FOUND"
        mock_uow.accounts.delete.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_delete_account_with_transactions(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns AccountError when account has transactions."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        mock_uow.accounts.get.return_value = account
        mock_uow.accounts.has_transactions.return_value = True

        result = asyncio.run(service.delete_account(account.id))

        assert isinstance(result, AccountError)
        assert result.code == "HAS_TRANSACTIONS"
        assert "Close it instead" in result.message
        mock_uow.accounts.delete.assert_not_called()
        mock_uow.commit.assert_not_called()


# --- Update Operation Tests ---


class TestUpdateOperations:
    """Tests for update operations."""

    def test_update_account_name_success(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Updates account name, collects event, commits."""
        account = Account.create_checking(
            user_id=user_id, name="Old Name", opening_balance=usd_balance
        )
        account.clear_events()
        mock_uow.accounts.get.return_value = account

        result = asyncio.run(service.update_account_name(account.id, "New Name"))

        assert isinstance(result, Account)
        assert result.name == "New Name"
        mock_uow.collect_events.assert_called_once()
        mock_uow.commit.assert_called_once()

        # Verify AccountUpdated event was collected
        assert len(mock_uow._collected_events) == 1
        event = mock_uow._collected_events[0]
        assert isinstance(event, AccountUpdated)
        assert event.field == "name"
        assert event.old_value == "Old Name"
        assert event.new_value == "New Name"

    def test_update_account_name_not_found(self, service: AccountService, mock_uow):
        """Returns AccountError when account not found."""
        account_id = AccountId.generate()
        mock_uow.accounts.get.return_value = None

        result = asyncio.run(service.update_account_name(account_id, "New Name"))

        assert isinstance(result, AccountError)
        assert result.code == "NOT_FOUND"
        mock_uow.commit.assert_not_called()

    def test_update_account_name_empty(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns AccountError for empty name."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        account.clear_events()
        mock_uow.accounts.get.return_value = account

        result = asyncio.run(service.update_account_name(account.id, ""))

        assert isinstance(result, AccountError)
        assert result.code == "VALIDATION_ERROR"
        assert "empty" in result.message.lower()
        mock_uow.commit.assert_not_called()

    def test_update_account_name_whitespace_only(
        self, service: AccountService, mock_uow, user_id: UserId, usd_balance: Money
    ):
        """Returns AccountError for whitespace-only name."""
        account = Account.create_checking(
            user_id=user_id, name="Checking", opening_balance=usd_balance
        )
        account.clear_events()
        mock_uow.accounts.get.return_value = account

        result = asyncio.run(service.update_account_name(account.id, "   "))

        assert isinstance(result, AccountError)
        assert result.code == "VALIDATION_ERROR"
        mock_uow.commit.assert_not_called()
