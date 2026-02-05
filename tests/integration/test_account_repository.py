"""Integration tests for Account repository.

Tests database persistence and retrieval of Account aggregate with all
value objects (Money, InstitutionDetails, RewardsBalance).

Note: After session.commit(), SQLAlchemy may modify the Account instance's
attribute types (e.g., AccountId -> str). Tests capture IDs before commit
to ensure correct comparisons with loaded entities.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from src.adapters.persistence.repositories.account import SqlAlchemyAccountRepository
from src.domain.exceptions import EntityNotFoundError
from src.domain.model.account import Account
from src.domain.model.account_types import AccountStatus, AccountSubtype, AccountType
from src.domain.model.entity_id import AccountId, HouseholdId, UserId
from src.domain.model.institution import InstitutionDetails
from src.domain.model.money import Money
from src.domain.model.rewards_balance import RewardsBalance


@pytest.fixture
def household_id(session):
    """Create a test household and return ID."""
    from src.adapters.persistence.orm.tables import households

    hh_id = HouseholdId.generate()
    session.execute(
        households.insert().values(
            id=str(hh_id),
            name="Test Household",
            owner_id=str(UserId.generate()),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    session.commit()
    return hh_id


@pytest.fixture
def user_id(session, household_id):
    """Create a test user and return ID."""
    from src.adapters.persistence.orm.tables import users

    uid = UserId.generate()
    session.execute(
        users.insert().values(
            id=str(uid),
            email=f"test-{uid}@example.com",
            display_name="Test User",
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$placeholder",
            household_id=str(household_id),
            email_verified=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    session.commit()
    return uid


@pytest.fixture
def repository(session):
    """Create repository with test session."""
    return SqlAlchemyAccountRepository(session)


@pytest.fixture
def usd_balance():
    """Standard USD balance for tests."""
    return Money(Decimal("1000.00"), "USD")


class TestAccountPersistence:
    """Test Account CRUD operations."""

    def test_add_and_get_checking_account(self, repository, session, user_id, household_id, usd_balance):
        """Can persist and retrieve a checking account."""
        account = Account.create_checking(
            user_id=user_id,
            name="Test Checking",
            opening_balance=usd_balance,
            household_id=household_id,
        )
        account_id = account.id  # Capture before commit
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.id == account_id
        assert loaded.name == "Test Checking"
        assert loaded.account_type == AccountType.CHECKING
        assert loaded.status == AccountStatus.ACTIVE
        assert loaded.opening_balance.amount == usd_balance.amount
        assert loaded.opening_balance.currency == usd_balance.currency

    def test_add_savings_account(self, repository, session, user_id, household_id, usd_balance):
        """Can persist savings account."""
        account = Account.create_savings(
            user_id=user_id,
            name="Emergency Fund",
            opening_balance=usd_balance,
            household_id=household_id,
        )
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.account_type == AccountType.SAVINGS

    def test_add_credit_card_with_limit(self, repository, session, user_id, household_id, usd_balance):
        """Can persist credit card with credit limit."""
        credit_limit = Money(Decimal("5000.00"), "USD")
        account = Account.create_credit_card(
            user_id=user_id,
            name="Visa Card",
            opening_balance=usd_balance,
            credit_limit=credit_limit,
            household_id=household_id,
        )
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.account_type == AccountType.CREDIT_CARD
        assert loaded.credit_limit is not None
        assert loaded.credit_limit.amount == credit_limit.amount
        assert loaded.credit_limit.currency == credit_limit.currency

    def test_add_loan_with_details(self, repository, session, user_id, household_id, usd_balance):
        """Can persist loan with APR, term, subtype."""
        account = Account.create_loan(
            user_id=user_id,
            name="Mortgage",
            opening_balance=usd_balance,
            subtype=AccountSubtype.MORTGAGE,
            apr=Decimal("0.0599"),
            term_months=360,
            household_id=household_id,
        )
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.account_type == AccountType.LOAN
        assert loaded.subtype == AccountSubtype.MORTGAGE
        assert loaded.apr == Decimal("0.0599")
        assert loaded.term_months == 360

    def test_add_brokerage_account(self, repository, session, user_id, household_id, usd_balance):
        """Can persist brokerage account."""
        account = Account.create_brokerage(
            user_id=user_id,
            name="Fidelity",
            opening_balance=usd_balance,
            household_id=household_id,
        )
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.account_type == AccountType.BROKERAGE

    def test_add_ira_account(self, repository, session, user_id, household_id, usd_balance):
        """Can persist IRA account with subtype."""
        account = Account.create_ira(
            user_id=user_id,
            name="Roth IRA",
            opening_balance=usd_balance,
            subtype=AccountSubtype.ROTH_IRA,
            household_id=household_id,
        )
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.account_type == AccountType.IRA
        assert loaded.subtype == AccountSubtype.ROTH_IRA

    def test_add_rewards_account(self, repository, session, user_id, household_id):
        """Can persist rewards account with RewardsBalance."""
        rewards = RewardsBalance(Decimal("50000"), "Alaska Miles")
        account = Account.create_rewards(
            user_id=user_id,
            name="Alaska Airlines",
            rewards_balance=rewards,
            household_id=household_id,
        )
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.account_type == AccountType.REWARDS
        assert loaded.rewards_balance is not None
        assert loaded.rewards_balance.value == Decimal("50000")
        assert loaded.rewards_balance.unit == "Alaska Miles"

    def test_add_account_with_institution(self, repository, session, user_id, household_id, usd_balance):
        """Can persist account with institution details."""
        institution = InstitutionDetails(
            name="Chase Bank",
            website="https://chase.com",
            phone="800-935-9935",
        )
        account = Account.create_checking(
            user_id=user_id,
            name="Chase Checking",
            opening_balance=usd_balance,
            institution=institution,
            household_id=household_id,
        )
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()
        session.expire_all()

        loaded = repository.get(account_id)

        assert loaded is not None
        assert loaded.institution is not None
        assert loaded.institution.name == "Chase Bank"
        assert loaded.institution.website == "https://chase.com"
        assert loaded.institution.phone == "800-935-9935"

    def test_get_nonexistent_returns_none(self, repository):
        """Getting nonexistent account returns None."""
        fake_id = AccountId.generate()
        result = repository.get(fake_id)
        assert result is None

    def test_get_or_raise_not_found(self, repository):
        """get_or_raise raises EntityNotFoundError."""
        fake_id = AccountId.generate()
        with pytest.raises(EntityNotFoundError):
            repository.get_or_raise(fake_id)

    def test_get_by_user(self, repository, session, user_id, household_id, usd_balance):
        """Can get all accounts for a user."""
        # Create multiple accounts
        checking = Account.create_checking(user_id, "Checking", usd_balance, household_id=household_id)
        savings = Account.create_savings(user_id, "Savings", usd_balance, household_id=household_id)
        checking.clear_events()
        savings.clear_events()

        repository.add(checking)
        repository.add(savings)
        session.commit()

        accounts = repository.get_by_user(user_id)

        assert len(accounts) == 2
        account_types = {a.account_type for a in accounts}
        assert AccountType.CHECKING in account_types
        assert AccountType.SAVINGS in account_types

    def test_get_by_user_with_type_filter(self, repository, session, user_id, household_id, usd_balance):
        """Can filter accounts by type."""
        checking = Account.create_checking(user_id, "Checking", usd_balance, household_id=household_id)
        savings = Account.create_savings(user_id, "Savings", usd_balance, household_id=household_id)
        checking.clear_events()
        savings.clear_events()

        repository.add(checking)
        repository.add(savings)
        session.commit()

        accounts = repository.get_by_user(user_id, account_type=AccountType.CHECKING)

        assert len(accounts) == 1
        assert accounts[0].account_type == AccountType.CHECKING

    def test_get_by_user_with_status_filter(self, repository, session, user_id, household_id, usd_balance):
        """Can filter accounts by status."""
        active = Account.create_checking(user_id, "Active", usd_balance, household_id=household_id)
        closed = Account.create_savings(user_id, "Closed", usd_balance, household_id=household_id)
        closed.close()
        active.clear_events()
        closed.clear_events()

        repository.add(active)
        repository.add(closed)
        session.commit()

        active_accounts = repository.get_by_user(user_id, status=AccountStatus.ACTIVE)
        closed_accounts = repository.get_by_user(user_id, status=AccountStatus.CLOSED)

        assert len(active_accounts) == 1
        assert len(closed_accounts) == 1

    def test_delete_account(self, repository, session, user_id, household_id, usd_balance):
        """Can delete an account."""
        account = Account.create_checking(user_id, "Delete Me", usd_balance, household_id=household_id)
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()

        # Verify it exists
        assert repository.get(account_id) is not None

        # Need to get fresh reference for delete
        to_delete = repository.get(account_id)
        repository.delete(to_delete)
        session.commit()

        # Verify it's gone
        assert repository.get(account_id) is None

    def test_has_transactions_returns_false(self, repository):
        """has_transactions returns False (placeholder until Phase 3)."""
        account_id = AccountId.generate()
        assert repository.has_transactions(account_id) is False


class TestAccountUpdate:
    """Test account update operations via repository."""

    def test_update_persists(self, repository, session, user_id, household_id, usd_balance):
        """Changes to loaded account persist on commit."""
        account = Account.create_checking(user_id, "Original", usd_balance, household_id=household_id)
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()

        # Load and modify
        loaded = repository.get(account_id)
        loaded.update_name("Updated", updated_by=user_id)
        loaded.clear_events()
        session.commit()

        # Reload and verify
        session.expire_all()
        reloaded = repository.get(account_id)
        assert reloaded.name == "Updated"

    def test_close_persists(self, repository, session, user_id, household_id, usd_balance):
        """Closing an account persists status change."""
        account = Account.create_checking(user_id, "Test", usd_balance, household_id=household_id)
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()

        loaded = repository.get(account_id)
        loaded.close()
        loaded.clear_events()
        session.commit()

        session.expire_all()
        reloaded = repository.get(account_id)
        assert reloaded.status == AccountStatus.CLOSED
        assert reloaded.closing_date is not None

    def test_reopen_persists(self, repository, session, user_id, household_id, usd_balance):
        """Reopening an account persists status change."""
        account = Account.create_checking(user_id, "Test", usd_balance, household_id=household_id)
        account.close()
        account_id = account.id
        account.clear_events()

        repository.add(account)
        session.commit()

        loaded = repository.get(account_id)
        loaded.reopen()
        loaded.clear_events()
        session.commit()

        session.expire_all()
        reloaded = repository.get(account_id)
        assert reloaded.status == AccountStatus.ACTIVE
        assert reloaded.closing_date is None
