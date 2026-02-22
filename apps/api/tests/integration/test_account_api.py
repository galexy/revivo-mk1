"""Integration tests for Account API endpoints.

Tests the full HTTP request/response cycle through FastAPI TestClient,
verifying that the API layer correctly handles account CRUD operations
with JWT authentication and household-scoped data access.

Auth flow: register -> verify email -> login -> use JWT bearer token.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from src.adapters.api.app import create_app
from src.adapters.persistence.orm.base import metadata
from src.adapters.persistence.orm.mappers import clear_mappers, start_mappers
from src.adapters.security.tokens import generate_verification_token


@pytest.fixture(scope="module")
def database_url():
    """Get test database URL."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finance_test",
    )


@pytest.fixture(scope="module")
def engine(database_url):
    """Create database engine for tests."""
    return create_engine(database_url, echo=False)


@pytest.fixture(scope="module")
def setup_database(engine, database_url):
    """Set up test database with fresh tables for account tests."""
    os.environ["DATABASE_URL"] = database_url

    clear_mappers()
    start_mappers()

    metadata.drop_all(engine)
    metadata.create_all(engine)

    yield

    clear_mappers()


@pytest.fixture
def client(setup_database):
    """Create test client with fresh app instance."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_user_data() -> dict:
    """Test user credentials with unique email."""
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "display_name": "Test User",
    }


@pytest.fixture
def registered_user(client: TestClient, test_user_data: dict) -> dict:
    """Register a test user and verify their email."""
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 202

    verification_token = generate_verification_token(test_user_data["email"])
    response = client.get(f"/auth/verify?token={verification_token}")
    assert response.status_code == 200

    return {**test_user_data, "user_id": response.json()["user_id"]}


@pytest.fixture
def auth_tokens(client: TestClient, registered_user: dict) -> dict:
    """Login and return tokens."""
    response = client.post(
        "/auth/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(auth_tokens: dict) -> dict:
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


class TestCreateEndpoints:
    """Test account creation endpoints."""

    def test_create_checking_account(self, client, auth_headers):
        """POST /api/v1/accounts/checking creates account."""
        response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "My Checking",
                "opening_balance": {"amount": "1000.00", "currency": "USD"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Checking"
        assert data["account_type"] == "checking"
        assert data["status"] == "active"
        assert "id" in data
        assert data["id"].startswith("acct_")

    def test_create_savings_account(self, client, auth_headers):
        """POST /api/v1/accounts/savings creates account."""
        response = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Emergency Fund",
                "opening_balance": {"amount": "5000.00", "currency": "USD"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "savings"

    def test_create_credit_card_account(self, client, auth_headers):
        """POST /api/v1/accounts/credit-card creates credit card."""
        response = client.post(
            "/api/v1/accounts/credit-card",
            json={
                "name": "Visa Card",
                "opening_balance": {"amount": "500.00", "currency": "USD"},
                "credit_limit": {"amount": "5000.00", "currency": "USD"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "credit_card"
        assert data["credit_limit"]["amount"] == "5000.0000"

    def test_create_loan_account(self, client, auth_headers):
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
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "loan"
        assert data["subtype"] == "mortgage"
        assert data["apr"] == "0.0599"
        assert data["term_months"] == 360

    def test_create_brokerage_account(self, client, auth_headers):
        """POST /api/v1/accounts/brokerage creates account."""
        response = client.post(
            "/api/v1/accounts/brokerage",
            json={
                "name": "Fidelity",
                "opening_balance": {"amount": "10000.00", "currency": "USD"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "brokerage"

    def test_create_ira_account(self, client, auth_headers):
        """POST /api/v1/accounts/ira creates IRA account."""
        response = client.post(
            "/api/v1/accounts/ira",
            json={
                "name": "Roth IRA",
                "opening_balance": {"amount": "6000.00", "currency": "USD"},
                "subtype": "roth_ira",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "ira"
        assert data["subtype"] == "roth_ira"

    def test_create_rewards_account(self, client, auth_headers):
        """POST /api/v1/accounts/rewards creates rewards account."""
        response = client.post(
            "/api/v1/accounts/rewards",
            json={
                "name": "Alaska Miles",
                "rewards_balance": {"value": "50000", "unit": "Alaska Miles"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "rewards"
        assert data["rewards_balance"]["value"] == "50000"
        assert data["rewards_balance"]["unit"] == "Alaska Miles"

    def test_create_account_validation_error(self, client, auth_headers):
        """Invalid request returns 422."""
        response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "",  # Empty name is invalid
                "opening_balance": {"amount": "1000", "currency": "USD"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 422


class TestReadEndpoints:
    """Test account read endpoints."""

    def test_list_accounts(self, client, auth_headers):
        """GET /api/v1/accounts returns account list."""
        # Create an account first
        client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "List Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )

        response = client.get("/api/v1/accounts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_accounts_with_type_filter(self, client, auth_headers):
        """GET /api/v1/accounts?type=checking filters by type."""
        # Create accounts of different types
        client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Checking for Filter",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings for Filter",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )

        response = client.get(
            "/api/v1/accounts", params={"type": "checking"}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for account in data["accounts"]:
            assert account["account_type"] == "checking"

    def test_list_accounts_with_status_filter(self, client, auth_headers):
        """GET /api/v1/accounts?status=active filters by status."""
        response = client.get(
            "/api/v1/accounts", params={"status": "active"}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for account in data["accounts"]:
            assert account["status"] == "active"

    def test_get_single_account(self, client, auth_headers):
        """GET /api/v1/accounts/{id} returns single account."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Get Test",
                "opening_balance": {"amount": "500", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = create_response.json()["id"]

        response = client.get(f"/api/v1/accounts/{account_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == account_id

    def test_get_nonexistent_account(self, client, auth_headers):
        """GET /api/v1/accounts/{id} returns 404 for nonexistent."""
        response = client.get(
            "/api/v1/accounts/acct_01h455vb4pex5vsknk084sn02q",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_invalid_id_format(self, client, auth_headers):
        """GET /api/v1/accounts/{id} returns 400 for invalid ID."""
        response = client.get("/api/v1/accounts/invalid-id", headers=auth_headers)

        assert response.status_code == 400


class TestLifecycleEndpoints:
    """Test account lifecycle endpoints."""

    def test_close_account(self, client, auth_headers):
        """POST /api/v1/accounts/{id}/close closes account."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Close Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/accounts/{account_id}/close", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "closed"
        assert response.json()["closing_date"] is not None

    def test_close_already_closed(self, client, auth_headers):
        """POST /api/v1/accounts/{id}/close on closed returns 409."""
        # Create and close
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Already Closed",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = create_response.json()["id"]
        client.post(f"/api/v1/accounts/{account_id}/close", headers=auth_headers)

        # Try to close again
        response = client.post(
            f"/api/v1/accounts/{account_id}/close", headers=auth_headers
        )

        assert response.status_code == 409

    def test_reopen_account(self, client, auth_headers):
        """POST /api/v1/accounts/{id}/reopen reopens closed account."""
        # Create and close
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Reopen Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = create_response.json()["id"]
        client.post(f"/api/v1/accounts/{account_id}/close", headers=auth_headers)

        response = client.post(
            f"/api/v1/accounts/{account_id}/reopen", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "active"
        assert response.json()["closing_date"] is None

    def test_reopen_not_closed(self, client, auth_headers):
        """POST /api/v1/accounts/{id}/reopen on active returns 409."""
        # Create active account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Active Account",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = create_response.json()["id"]

        # Try to reopen active account
        response = client.post(
            f"/api/v1/accounts/{account_id}/reopen", headers=auth_headers
        )

        assert response.status_code == 409

    def test_delete_account(self, client, auth_headers):
        """DELETE /api/v1/accounts/{id} deletes account."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Delete Test",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/accounts/{account_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/accounts/{account_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent(self, client, auth_headers):
        """DELETE /api/v1/accounts/{id} returns 404 for nonexistent."""
        response = client.delete(
            "/api/v1/accounts/acct_01h455vb4pex5vsknk084sn02q",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestUpdateEndpoints:
    """Test account update endpoints."""

    def test_update_name(self, client, auth_headers):
        """PATCH /api/v1/accounts/{id} updates account name."""
        # Create account
        create_response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Original Name",
                "opening_balance": {"amount": "100", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/accounts/{account_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_update_nonexistent(self, client, auth_headers):
        """PATCH /api/v1/accounts/{id} returns 404 for nonexistent."""
        response = client.patch(
            "/api/v1/accounts/acct_01h455vb4pex5vsknk084sn02q",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestHouseholdIsolation:
    """Verify that users cannot access data from other households."""

    def _create_second_user(self, client: TestClient) -> dict:
        """Register and authenticate a second user (different household)."""
        user_data = {
            "email": f"other_{uuid.uuid4().hex[:8]}@example.com",
            "password": "OtherPassword123!",
            "display_name": "Other User",
        }
        # Register
        client.post("/auth/register", json=user_data)
        # Verify email
        token = generate_verification_token(user_data["email"])
        client.get(f"/auth/verify?token={token}")
        # Login
        response = client.post(
            "/auth/token",
            data={"username": user_data["email"], "password": user_data["password"]},
        )
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_cannot_access_other_household_account(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Accessing another household's account returns 404."""
        # Create account with first user
        response = client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "My Account",
                "opening_balance": {"amount": "100.00", "currency": "USD"},
            },
            headers=auth_headers,
        )
        account_id = response.json()["id"]

        # Login as second user (different household)
        other_headers = self._create_second_user(client)

        # Try to access first user's account -> 404
        response = client.get(f"/api/v1/accounts/{account_id}", headers=other_headers)
        assert response.status_code == 404

    def test_cannot_list_other_household_accounts(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Listing accounts only shows own household's accounts."""
        # Create account with first user
        client.post(
            "/api/v1/accounts/checking",
            json={
                "name": "Hidden Account",
                "opening_balance": {"amount": "50.00", "currency": "USD"},
            },
            headers=auth_headers,
        )

        # Login as second user
        other_headers = self._create_second_user(client)

        # List accounts as second user -> should be empty
        response = client.get("/api/v1/accounts", headers=other_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0
