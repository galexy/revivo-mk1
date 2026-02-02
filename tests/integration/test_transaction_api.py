"""Integration tests for Transaction API endpoints.

Tests the full HTTP request/response cycle through FastAPI TestClient,
verifying that the API layer correctly handles transaction CRUD operations.

Covers:
- Create expense with single split
- Create split transaction (multiple categories)
- Create transfer with mirror creation
- Split validation (sum to amount)
- Get single transaction
- Filter by account, date range
- Full-text search
- Status progression (pending -> cleared -> reconciled)
- Delete transaction
- Delete source deletes mirrors
- Cannot delete mirror directly
- Auto-create payee

Note: Uses the placeholder user ID from the API until Phase 4 authentication.
"""

import os
from datetime import date
from decimal import Decimal

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
    """Set up test database with fresh tables."""
    os.environ["DATABASE_URL"] = database_url

    clear_mappers()
    start_mappers()

    metadata.drop_all(engine)
    metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
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

    metadata.drop_all(engine)
    clear_mappers()


@pytest.fixture
def client(setup_database):
    """Create test client with fresh app instance."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_account(client):
    """Create a test account for transactions."""
    response = client.post(
        "/api/v1/accounts/checking",
        json={
            "name": "Test Checking",
            "opening_balance": {"amount": "1000.00", "currency": "USD"},
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_category(client):
    """Create a test category for transactions."""
    response = client.post(
        "/api/v1/categories",
        json={"name": "Groceries"},
    )
    assert response.status_code == 201
    return response.json()


class TestTransactionAPI:
    """Tests for /api/v1/transactions endpoints."""

    def test_create_simple_expense(self, client, test_account, test_category):
        """POST /transactions should create expense with single split."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-50.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-50.00", "currency": "USD"},
                        "category_id": test_category["id"],
                        "memo": "Weekly groceries",
                    }
                ],
                "payee_name": "Whole Foods",
                "memo": "Weekly shopping",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"].startswith("txn_")
        assert data["account_id"] == test_account["id"]
        assert Decimal(data["amount"]["amount"]) == Decimal("-50.00")
        assert data["payee_name"] == "Whole Foods"
        assert len(data["splits"]) == 1
        assert data["splits"][0]["category_id"] == test_category["id"]
        assert data["status"] == "pending"
        assert data["is_mirror"] is False

    def test_create_split_transaction(self, client, test_account):
        """POST /transactions should create multi-split transaction."""
        # Create two categories
        cat1 = client.post("/api/v1/categories", json={"name": "Food Items"}).json()
        cat2 = client.post("/api/v1/categories", json={"name": "Household Items"}).json()

        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-70.00", "currency": "USD"},
                        "category_id": cat1["id"],
                        "memo": "Food items",
                    },
                    {
                        "amount": {"amount": "-30.00", "currency": "USD"},
                        "category_id": cat2["id"],
                        "memo": "Household items",
                    },
                ],
                "payee_name": "Target",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["splits"]) == 2
        split_amounts = [Decimal(s["amount"]["amount"]) for s in data["splits"]]
        assert Decimal("-70.00") in split_amounts
        assert Decimal("-30.00") in split_amounts

    def test_create_transfer_creates_mirror(self, client, test_account):
        """POST /transactions with transfer split should create mirror."""
        # Create second account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create transfer from checking to savings
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-500.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                        "memo": "Monthly savings transfer",
                    }
                ],
                "memo": "Transfer to savings",
            },
        )

        assert response.status_code == 201
        source_txn = response.json()
        assert source_txn["is_mirror"] is False
        assert source_txn["splits"][0]["transfer_account_id"] == savings["id"]

        # Check for mirror in savings account
        savings_txns = client.get(
            f"/api/v1/transactions?account_id={savings['id']}"
        ).json()

        # Should have one transaction (the mirror)
        assert len(savings_txns["transactions"]) == 1
        mirror = savings_txns["transactions"][0]
        assert mirror["is_mirror"] is True
        assert mirror["source_transaction_id"] == source_txn["id"]
        # Mirror amount is positive (incoming)
        assert Decimal(mirror["amount"]["amount"]) == Decimal("500.00")

    def test_splits_must_sum_to_amount(self, client, test_account, test_category):
        """POST /transactions should reject if splits don't sum to amount."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-50.00", "currency": "USD"},  # Only 50, not 100
                        "category_id": test_category["id"],
                    }
                ],
            },
        )

        assert response.status_code == 400
        assert "INVALID_SPLITS" in response.json()["detail"]["code"]

    def test_cannot_self_transfer(self, client, test_account):
        """POST /transactions should reject transfer to same account."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "transfer_account_id": test_account["id"],  # Same account!
                    }
                ],
            },
        )

        assert response.status_code == 400
        assert "same account" in response.json()["detail"]["message"].lower()

    def test_get_transaction(self, client, test_account, test_category):
        """GET /transactions/{id} should return transaction with splits."""
        # Create transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-25.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-25.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )
        txn_id = create_response.json()["id"]

        # Get transaction
        response = client.get(f"/api/v1/transactions/{txn_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == txn_id
        assert len(data["splits"]) == 1

    def test_filter_by_account(self, client, test_account, test_category):
        """GET /transactions?account_id= should filter by account."""
        # Create transaction
        client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-10.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-10.00", "currency": "USD"}, "category_id": test_category["id"]}],
            },
        )

        # Filter
        response = client.get(f"/api/v1/transactions?account_id={test_account['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(t["account_id"] == test_account["id"] for t in data["transactions"])

    def test_filter_by_date_range(self, client, test_account, test_category):
        """GET /transactions?date_from=&date_to= should filter by date."""
        today = date.today()

        # Create transaction for today
        client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": today.isoformat(),
                "amount": {"amount": "-5.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-5.00", "currency": "USD"}, "category_id": test_category["id"]}],
            },
        )

        # Filter for today
        response = client.get(
            f"/api/v1/transactions?date_from={today.isoformat()}&date_to={today.isoformat()}"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(t["effective_date"] == today.isoformat() for t in data["transactions"])

    def test_search_transactions(self, client, test_account, test_category):
        """GET /transactions?search= should full-text search."""
        # Create transaction with specific payee
        unique_payee = f"UniqueSearchPayee{date.today().isoformat().replace('-', '')}"
        client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-99.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-99.00", "currency": "USD"}, "category_id": test_category["id"]}],
                "payee_name": unique_payee,
            },
        )

        # Search
        response = client.get(f"/api/v1/transactions?search={unique_payee}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(unique_payee in (t.get("payee_name") or "") for t in data["transactions"])

    def test_mark_cleared(self, client, test_account, test_category):
        """POST /transactions/{id}/clear should mark as cleared."""
        # Create transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-15.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-15.00", "currency": "USD"}, "category_id": test_category["id"]}],
            },
        )
        txn_id = create_response.json()["id"]
        assert create_response.json()["status"] == "pending"

        # Mark cleared
        response = client.post(f"/api/v1/transactions/{txn_id}/clear")

        assert response.status_code == 200
        assert response.json()["status"] == "cleared"

    def test_mark_reconciled(self, client, test_account, test_category):
        """POST /transactions/{id}/reconcile should mark as reconciled."""
        # Create and clear transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-20.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-20.00", "currency": "USD"}, "category_id": test_category["id"]}],
            },
        )
        txn_id = create_response.json()["id"]

        # Clear first
        client.post(f"/api/v1/transactions/{txn_id}/clear")

        # Then reconcile
        response = client.post(f"/api/v1/transactions/{txn_id}/reconcile")

        assert response.status_code == 200
        assert response.json()["status"] == "reconciled"

    def test_delete_transaction(self, client, test_account, test_category):
        """DELETE /transactions/{id} should delete transaction."""
        # Create transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-30.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-30.00", "currency": "USD"}, "category_id": test_category["id"]}],
            },
        )
        txn_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/transactions/{txn_id}")
        assert response.status_code == 204

        # Verify gone
        get_response = client.get(f"/api/v1/transactions/{txn_id}")
        assert get_response.status_code == 404

    def test_delete_source_deletes_mirrors(self, client, test_account):
        """DELETE source transaction should also delete its mirrors."""
        # Create savings account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings2",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create transfer
        source = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-200.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-200.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        ).json()

        # Get mirror
        savings_txns = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(savings_txns["transactions"]) == 1
        mirror_id = savings_txns["transactions"][0]["id"]

        # Delete source
        response = client.delete(f"/api/v1/transactions/{source['id']}")
        assert response.status_code == 204

        # Verify mirror also gone
        mirror_response = client.get(f"/api/v1/transactions/{mirror_id}")
        assert mirror_response.status_code == 404

    def test_cannot_delete_mirror_directly(self, client, test_account):
        """DELETE mirror transaction should fail."""
        # Create savings and transfer
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings3",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-150.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-150.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        )

        # Get mirror
        savings_txns = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        mirror_id = savings_txns["transactions"][0]["id"]

        # Try to delete mirror directly
        response = client.delete(f"/api/v1/transactions/{mirror_id}")

        assert response.status_code == 400
        assert "CANNOT_DELETE_MIRROR" in response.json()["detail"]["code"]

    def test_auto_creates_payee(self, client, test_account, test_category):
        """Creating transaction with new payee should auto-create it."""
        unique_payee = f"NewPayee_{date.today().isoformat()}"

        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-45.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-45.00", "currency": "USD"}, "category_id": test_category["id"]}],
                "payee_name": unique_payee,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["payee_name"] == unique_payee
        assert data["payee_id"] is not None
        assert data["payee_id"].startswith("payee_")

    def test_get_nonexistent_transaction(self, client):
        """GET /transactions/{id} returns 404 for nonexistent."""
        response = client.get("/api/v1/transactions/txn_01h455vb4pex5vsknk084sn02q")
        assert response.status_code == 404

    def test_update_transaction_memo(self, client, test_account, test_category):
        """PATCH /transactions/{id} should update memo."""
        # Create transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-60.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-60.00", "currency": "USD"}, "category_id": test_category["id"]}],
                "memo": "Original memo",
            },
        )
        txn_id = create_response.json()["id"]

        # Update memo
        response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={"memo": "Updated memo"},
        )

        assert response.status_code == 200
        assert response.json()["memo"] == "Updated memo"

    def test_create_income_transaction(self, client, test_account, test_category):
        """POST /transactions should create income with positive amount."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "2500.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "2500.00", "currency": "USD"},
                        "category_id": test_category["id"],
                        "memo": "Salary",
                    }
                ],
                "payee_name": "Employer Inc",
                "memo": "Monthly paycheck",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["amount"]["amount"]) == Decimal("2500.00")
        assert data["payee_name"] == "Employer Inc"
