"""Integration tests for Account API endpoints.

Tests the full HTTP request/response cycle through FastAPI TestClient,
verifying that the API layer correctly handles account CRUD operations.

Note: Uses the placeholder user ID from the API until Phase 4 authentication.
These tests create fresh database tables for each test module.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.api.app import create_app
from src.adapters.persistence.orm.base import metadata
from src.adapters.persistence.orm.mappers import clear_mappers, start_mappers
from src.adapters.persistence.orm.tables import users


@pytest.fixture(scope="module")
def database_url():
    """Get test database URL."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/finance_test",
    )


@pytest.fixture(scope="module")
def engine(database_url):
    """Create database engine for tests."""
    return create_engine(database_url, echo=False)


@pytest.fixture(scope="module")
def setup_database(engine, database_url):
    """Set up test database with fresh tables.

    Creates tables, registers mappers, and creates the placeholder user
    that the API uses for authentication.
    """
    # Set environment variables for the API to use
    os.environ["DATABASE_URL"] = database_url

    # Clear any existing mappers and recreate
    clear_mappers()
    start_mappers()

    # Drop and recreate tables
    metadata.drop_all(engine)
    metadata.create_all(engine)

    # Create the placeholder user that the API uses
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # This is the placeholder user ID from src/adapters/api/routes/accounts.py
        uid = "user_01h455vb4pex5vsknk084sn02q"
        session.execute(
            users.insert().values(
                id=uid,
                email="placeholder@example.com",
                email_verified=True,
            )
        )
        session.commit()
    finally:
        session.close()

    yield

    # Note: Don't drop tables on cleanup - other tests depend on them
    clear_mappers()


@pytest.fixture
def client(setup_database):
    """Create test client with fresh app instance."""
    app = create_app()
    return TestClient(app)


class TestCreateEndpoints:
    """Test account creation endpoints."""

    def test_create_checking_account(self, client):
        """POST /api/v1/accounts/checking creates account."""
        response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "My Checking",
                "opening_balance": {"amount": "1000.00", "currency": "USD"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Checking"
        assert data["account_type"] == "checking"
        assert data["status"] == "active"
        assert "id" in data
        assert data["id"].startswith("acct_")

    def test_create_savings_account(self, client):
        """POST /api/v1/accounts/savings creates account."""
        response = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Emergency Fund",
                "opening_balance": {"amount": "5000.00", "currency": "USD"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "savings"

    def test_create_credit_card_account(self, client):
        """POST /api/v1/accounts/credit-card creates credit card."""
        response = client.post(
            "/api/v1/accounts/credit-card",
            json={
                "name": "Visa Card",
                "opening_balance": {"amount": "500.00", "currency": "USD"},
                "credit_limit": {"amount": "5000.00", "currency": "USD"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "credit_card"
        assert data["credit_limit"]["amount"] == "5000.0000"

    def test_create_loan_account(self, client):
        """POST /api/v1/accounts/loan creates loan with details."""
        response = client.post(
            "/api/v1/accounts/loan",
            json={
                "name": "Mortgage",
                "opening_balance": {"amount": "300000.00", "currency": "USD"},
                "subtype": "mortgage",
                "apr": "0.0599",
                "term_months": 360,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "loan"
        assert data["subtype"] == "mortgage"
        assert data["apr"] == "0.0599"
        assert data["term_months"] == 360

    def test_create_brokerage_account(self, client):
        """POST /api/v1/accounts/brokerage creates account."""
        response = client.post(
            "/api/v1/accounts/brokerage",
            json={
                "name": "Fidelity",
                "opening_balance": {"amount": "10000.00", "currency": "USD"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "brokerage"

    def test_create_ira_account(self, client):
        """POST /api/v1/accounts/ira creates IRA account."""
        response = client.post(
            "/api/v1/accounts/ira",
            json={
                "name": "Roth IRA",
                "opening_balance": {"amount": "6000.00", "currency": "USD"},
                "subtype": "roth_ira",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "ira"
        assert data["subtype"] == "roth_ira"

    def test_create_rewards_account(self, client):
        """POST /api/v1/accounts/rewards creates rewards account."""
        response = client.post(
            "/api/v1/accounts/rewards",
            json={
                "name": "Alaska Miles",
                "rewards_balance": {"value": "50000", "unit": "Alaska Miles"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "rewards"
        assert data["rewards_balance"]["value"] == "50000"
        assert data["rewards_balance"]["unit"] == "Alaska Miles"

    def test_create_account_validation_error(self, client):
        """Invalid request returns 422."""
        response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "",  # Empty name is invalid
                "opening_balance": {"amount": "1000", "currency": "USD"},
            },
        )

        assert response.status_code == 422


class TestReadEndpoints:
    """Test account read endpoints."""

    def test_list_accounts(self, client):
        """GET /api/v1/accounts returns account list."""
        # Create an account first
        client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "List Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )

        response = client.get("/api/v1/accounts")

        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_accounts_with_type_filter(self, client):
        """GET /api/v1/accounts?type=checking filters by type."""
        # Create accounts of different types
        client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Checking for Filter",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )
        client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings for Filter",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )

        response = client.get("/api/v1/accounts", params={"type": "checking"})

        assert response.status_code == 200
        data = response.json()
        for account in data["accounts"]:
            assert account["account_type"] == "checking"

    def test_list_accounts_with_status_filter(self, client):
        """GET /api/v1/accounts?status=active filters by status."""
        response = client.get("/api/v1/accounts", params={"status": "active"})

        assert response.status_code == 200
        data = response.json()
        for account in data["accounts"]:
            assert account["status"] == "active"

    def test_get_single_account(self, client):
        """GET /api/v1/accounts/{id} returns single account."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Get Test",
                "opening_balance": {"amount": "500", "currency": "USD"},
            },
        )
        account_id = create_response.json()["id"]

        response = client.get(f"/api/v1/accounts/{account_id}")

        assert response.status_code == 200
        assert response.json()["id"] == account_id

    def test_get_nonexistent_account(self, client):
        """GET /api/v1/accounts/{id} returns 404 for nonexistent."""
        response = client.get("/api/v1/accounts/acct_01h455vb4pex5vsknk084sn02q")

        assert response.status_code == 404

    def test_get_invalid_id_format(self, client):
        """GET /api/v1/accounts/{id} returns 400 for invalid ID."""
        response = client.get("/api/v1/accounts/invalid-id")

        assert response.status_code == 400


class TestLifecycleEndpoints:
    """Test account lifecycle endpoints."""

    def test_close_account(self, client):
        """POST /api/v1/accounts/{id}/close closes account."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Close Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )
        account_id = create_response.json()["id"]

        response = client.post(f"/api/v1/accounts/{account_id}/close")

        assert response.status_code == 200
        assert response.json()["status"] == "closed"
        assert response.json()["closing_date"] is not None

    def test_close_already_closed(self, client):
        """POST /api/v1/accounts/{id}/close on closed returns 409."""
        # Create and close
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Already Closed",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )
        account_id = create_response.json()["id"]
        client.post(f"/api/v1/accounts/{account_id}/close")

        # Try to close again
        response = client.post(f"/api/v1/accounts/{account_id}/close")

        assert response.status_code == 409

    def test_reopen_account(self, client):
        """POST /api/v1/accounts/{id}/reopen reopens closed account."""
        # Create and close
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Reopen Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )
        account_id = create_response.json()["id"]
        client.post(f"/api/v1/accounts/{account_id}/close")

        response = client.post(f"/api/v1/accounts/{account_id}/reopen")

        assert response.status_code == 200
        assert response.json()["status"] == "active"
        assert response.json()["closing_date"] is None

    def test_reopen_not_closed(self, client):
        """POST /api/v1/accounts/{id}/reopen on active returns 409."""
        # Create active account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Active Account",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )
        account_id = create_response.json()["id"]

        # Try to reopen active account
        response = client.post(f"/api/v1/accounts/{account_id}/reopen")

        assert response.status_code == 409

    def test_delete_account(self, client):
        """DELETE /api/v1/accounts/{id} deletes account."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Delete Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )
        account_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/accounts/{account_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/accounts/{account_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent(self, client):
        """DELETE /api/v1/accounts/{id} returns 404 for nonexistent."""
        response = client.delete("/api/v1/accounts/acct_01h455vb4pex5vsknk084sn02q")

        assert response.status_code == 404


class TestUpdateEndpoints:
    """Test account update endpoints."""

    def test_update_name(self, client):
        """PATCH /api/v1/accounts/{id} updates account name."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Original Name",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
        )
        account_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/accounts/{account_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_update_nonexistent(self, client):
        """PATCH /api/v1/accounts/{id} returns 404 for nonexistent."""
        response = client.patch(
            "/api/v1/accounts/acct_01h455vb4pex5vsknk084sn02q",
            json={"name": "New Name"},
        )

        assert response.status_code == 404
