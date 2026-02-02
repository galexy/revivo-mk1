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
from collections.abc import Generator
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.api.app import create_app
from src.adapters.persistence.orm.base import metadata
from src.adapters.persistence.orm.mappers import clear_mappers, start_mappers
from src.adapters.persistence.orm.tables import users

# Type alias for fixture return types
JsonDict = dict[str, Any]


@pytest.fixture(scope="module")
def database_url() -> str:
    """Get test database URL."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/finance_test",
    )


@pytest.fixture(scope="module")
def engine(database_url: str) -> Engine:
    """Create database engine for tests."""
    return create_engine(database_url, echo=False)


@pytest.fixture(scope="module")
def setup_database(engine: Engine, database_url: str) -> Generator[None, None, None]:
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

    # Note: Don't drop tables on cleanup - other tests depend on them
    clear_mappers()


@pytest.fixture
def client(setup_database: None) -> TestClient:
    """Create test client with fresh app instance."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_account(client: TestClient) -> JsonDict:
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
def test_category(client: TestClient) -> JsonDict:
    """Create a test category for transactions."""
    response = client.post(
        "/api/v1/categories",
        json={"name": "Groceries"},
    )
    assert response.status_code == 201
    return response.json()


class TestTransactionAPI:
    """Tests for /api/v1/transactions endpoints."""

    def test_create_simple_expense(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_create_split_transaction(self, client: TestClient, test_account: JsonDict) -> None:
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

    def test_create_transfer_creates_mirror(self, client: TestClient, test_account: JsonDict) -> None:
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

    def test_splits_must_sum_to_amount(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_cannot_self_transfer(self, client: TestClient, test_account: JsonDict) -> None:
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

    def test_get_transaction(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_filter_by_account(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_filter_by_date_range(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_search_transactions(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_mark_cleared(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_mark_reconciled(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_delete_transaction(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_delete_source_deletes_mirrors(self, client: TestClient, test_account: JsonDict) -> None:
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

    def test_cannot_delete_mirror_directly(self, client: TestClient, test_account: JsonDict) -> None:
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

    def test_auto_creates_payee(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_get_nonexistent_transaction(self, client: TestClient) -> None:
        """GET /transactions/{id} returns 404 for nonexistent."""
        response = client.get("/api/v1/transactions/txn_01h455vb4pex5vsknk084sn02q")
        assert response.status_code == 404

    def test_update_transaction_memo(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    def test_create_income_transaction(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
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

    # ===== Edge Case Tests (from UAT) =====

    def test_mixed_category_and_transfer_splits(self, client: TestClient, test_account: JsonDict) -> None:
        """Transaction with both category and transfer splits should work."""
        # Create credit card account and category
        cc_response = client.post(
            "/api/v1/accounts/credit-card",
            json={
                "name": "Credit Card Mixed",
                "opening_balance": {"amount": "-1000.00", "currency": "USD"},
                "credit_limit": {"amount": "5000.00", "currency": "USD"},
            },
        )
        assert cc_response.status_code == 201
        cc_account = cc_response.json()

        cashback_cat = client.post(
            "/api/v1/categories",
            json={"name": "Cash Back Rewards"},
        ).json()

        # Create transaction: -500 transfer to CC, +20 cash back = -480 net
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-480.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-500.00", "currency": "USD"},
                        "transfer_account_id": cc_account["id"],
                    },
                    {
                        "amount": {"amount": "20.00", "currency": "USD"},
                        "category_id": cashback_cat["id"],
                    },
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["splits"]) == 2

        # Verify mirror created for transfer portion
        cc_txns = client.get(f"/api/v1/transactions?account_id={cc_account['id']}").json()
        assert len(cc_txns["transactions"]) == 1
        assert cc_txns["transactions"][0]["is_mirror"] is True

    def test_positive_transfer_split_rejected(self, client: TestClient, test_account: JsonDict) -> None:
        """Transfer splits must be negative (outgoing from source)."""
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings Positive Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "100.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        )

        assert response.status_code == 400

    def test_mixed_income_expense_splits(self, client: TestClient, test_account: JsonDict) -> None:
        """Transaction can have both positive and negative splits (refund scenario)."""
        refund_cat = client.post("/api/v1/categories", json={"name": "Refunds"}).json()
        fee_cat = client.post("/api/v1/categories", json={"name": "Fees"}).json()

        # +100 refund, -15 restocking fee = +85 net
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "85.00", "currency": "USD"},
                "splits": [
                    {"amount": {"amount": "100.00", "currency": "USD"}, "category_id": refund_cat["id"]},
                    {"amount": {"amount": "-15.00", "currency": "USD"}, "category_id": fee_cat["id"]},
                ],
            },
        )

        assert response.status_code == 201
        assert len(response.json()["splits"]) == 2

    def test_empty_splits_rejected(self, client: TestClient, test_account: JsonDict) -> None:
        """Transaction must have at least one split."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-50.00", "currency": "USD"},
                "splits": [],
            },
        )

        assert response.status_code in (400, 422)

    def test_cannot_reconcile_pending_transaction(self, client: TestClient, test_account: JsonDict, test_category: JsonDict) -> None:
        """Must clear before reconciling."""
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-25.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-25.00", "currency": "USD"}, "category_id": test_category["id"]}],
            },
        )
        txn_id = create_response.json()["id"]

        response = client.post(f"/api/v1/transactions/{txn_id}/reconcile")

        assert response.status_code == 400
        assert "INVALID_STATUS_TRANSITION" in response.json()["detail"]["code"]

    def test_cannot_patch_mirror_directly(self, client: TestClient, test_account: JsonDict) -> None:
        """Mirror transactions cannot be modified directly."""
        savings = client.post(
            "/api/v1/accounts/savings",
            json={"name": "Savings Mirror Test", "opening_balance": {"amount": "0.00", "currency": "USD"}},
        ).json()

        client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-300.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-300.00", "currency": "USD"}, "transfer_account_id": savings["id"]}],
            },
        )

        savings_txns = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        mirror_id = savings_txns["transactions"][0]["id"]

        response = client.patch(f"/api/v1/transactions/{mirror_id}", json={"memo": "Try modify"})

        assert response.status_code == 400
        assert "CANNOT_MODIFY_MIRROR" in response.json()["detail"]["code"]

    def test_update_transfer_syncs_mirror(self, client: TestClient, test_account: JsonDict) -> None:
        """Updating source transfer amount should update mirror."""
        savings = client.post(
            "/api/v1/accounts/savings",
            json={"name": "Savings Sync Test", "opening_balance": {"amount": "0.00", "currency": "USD"}},
        ).json()

        source = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-500.00", "currency": "USD"}, "transfer_account_id": savings["id"]}],
            },
        ).json()

        # Update to -600
        client.patch(
            f"/api/v1/transactions/{source['id']}",
            json={
                "amount": {"amount": "-600.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-600.00", "currency": "USD"}, "transfer_account_id": savings["id"]}],
            },
        )

        savings_txns = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert Decimal(savings_txns["transactions"][0]["amount"]["amount"]) == Decimal("600.00")

    def test_transaction_with_subcategory(self, client: TestClient, test_account: JsonDict) -> None:
        """Can assign transaction to subcategory."""
        parent = client.post("/api/v1/categories", json={"name": "Food & Dining"}).json()
        child = client.post("/api/v1/categories", json={"name": "Restaurants", "parent_id": parent["id"]}).json()

        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-45.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-45.00", "currency": "USD"}, "category_id": child["id"]}],
            },
        )

        assert response.status_code == 201
        assert response.json()["splits"][0]["category_id"] == child["id"]

    def test_split_with_both_category_and_transfer_rejected(self, client: TestClient, test_account: JsonDict) -> None:
        """Single split cannot have both category_id and transfer_account_id."""
        cat = client.post("/api/v1/categories", json={"name": "Invalid Split"}).json()
        savings = client.post(
            "/api/v1/accounts/savings",
            json={"name": "Savings Both Test", "opening_balance": {"amount": "0.00", "currency": "USD"}},
        ).json()

        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": cat["id"],
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        )

        assert response.status_code == 400

    def test_multiple_transfers_in_transaction(self, client: TestClient, test_account: JsonDict) -> None:
        """Can split transfer across multiple destination accounts."""
        savings = client.post(
            "/api/v1/accounts/savings",
            json={"name": "Savings Multi", "opening_balance": {"amount": "0.00", "currency": "USD"}},
        ).json()
        investment = client.post(
            "/api/v1/accounts/brokerage",
            json={"name": "Investment Multi", "opening_balance": {"amount": "0.00", "currency": "USD"}},
        ).json()

        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-1000.00", "currency": "USD"},
                "splits": [
                    {"amount": {"amount": "-600.00", "currency": "USD"}, "transfer_account_id": savings["id"]},
                    {"amount": {"amount": "-400.00", "currency": "USD"}, "transfer_account_id": investment["id"]},
                ],
            },
        )

        assert response.status_code == 201

        savings_txns = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        invest_txns = client.get(f"/api/v1/transactions?account_id={investment['id']}").json()

        assert len(savings_txns["transactions"]) == 1
        assert len(invest_txns["transactions"]) == 1


class TestTransactionValidationErrors:
    """Tests for proper 400/422 responses on validation errors."""

    def test_invalid_account_id_returns_400(self, client: TestClient, setup_database: None) -> None:
        """Invalid account ID format should return 400, not 500."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": "invalid_format",
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-100.00", "currency": "USD"}}],
            },
        )
        assert response.status_code == 400
        assert "INVALID_ID_FORMAT" in response.json().get("detail", {}).get("code", "")

    def test_invalid_category_id_returns_400(self, client: TestClient, test_account: JsonDict) -> None:
        """Invalid category ID format should return 400, not 500."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": "invalid_format",
                    }
                ],
            },
        )
        assert response.status_code == 400

    def test_empty_string_category_id_returns_422(self, client: TestClient, test_account: JsonDict) -> None:
        """Empty string category_id should return 422 (Pydantic validation)."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": "",  # Empty string - should be rejected
                    }
                ],
            },
        )
        assert response.status_code == 422
        # Pydantic error includes the field name
        assert "category_id" in str(response.json())

    def test_empty_string_transfer_account_id_returns_422(
        self, client: TestClient, test_account: JsonDict
    ) -> None:
        """Empty string transfer_account_id should return 422."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "transfer_account_id": "",  # Empty string - should be rejected
                    }
                ],
            },
        )
        assert response.status_code == 422
        assert "transfer_account_id" in str(response.json())


class TestSplitIdentity:
    """Tests for split ID persistence and PATCH semantics."""

    def test_transaction_response_includes_split_ids(
        self, client: TestClient, test_account: JsonDict
    ) -> None:
        """Transaction response should include split IDs."""
        # Create transaction
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-100.00", "currency": "USD"}}],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["splits"]) == 1
        assert "id" in data["splits"][0]
        assert data["splits"][0]["id"].startswith("split_")

    def test_split_ids_persist_across_get(self, client: TestClient, test_account: JsonDict) -> None:
        """Split IDs should persist when getting transaction."""
        # Create
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [{"amount": {"amount": "-100.00", "currency": "USD"}}],
            },
        )
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # Get
        get_response = client.get(f"/api/v1/transactions/{txn_id}")
        assert get_response.status_code == 200
        assert get_response.json()["splits"][0]["id"] == split_id

    def test_patch_with_split_id_updates_specific_split(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """PATCH with split ID should update that specific split."""
        # Create transaction with two splits
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {"amount": {"amount": "-60.00", "currency": "USD"}},
                    {"amount": {"amount": "-40.00", "currency": "USD"}},
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        splits = create_response.json()["splits"]
        split1_id = splits[0]["id"]
        split2_id = splits[1]["id"]

        # PATCH - update first split, keep second
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split1_id,
                        "amount": {"amount": "-70.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    },
                    {
                        "id": split2_id,
                        "amount": {"amount": "-30.00", "currency": "USD"},
                    },
                ],
            },
        )
        assert patch_response.status_code == 200

        # Verify IDs preserved
        updated = patch_response.json()
        assert updated["splits"][0]["id"] == split1_id
        assert updated["splits"][1]["id"] == split2_id
        # Verify amounts changed
        split_amounts = {s["id"]: Decimal(s["amount"]["amount"]) for s in updated["splits"]}
        assert split_amounts[split1_id] == Decimal("-70.00")
        assert split_amounts[split2_id] == Decimal("-30.00")

    def test_mirror_transaction_has_source_split_id(self, client: TestClient, test_account: JsonDict) -> None:
        """Mirror transactions should have source_split_id populated."""
        # Create savings account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings SplitID Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create transfer
        source = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-250.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-250.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        ).json()

        # Get source split ID
        source_split_id = source["splits"][0]["id"]
        assert source_split_id.startswith("split_")

        # Get mirror transaction
        savings_txns = client.get(
            f"/api/v1/transactions?account_id={savings['id']}"
        ).json()
        assert len(savings_txns["transactions"]) == 1
        mirror = savings_txns["transactions"][0]

        # Verify mirror has source_split_id linking to source split
        assert mirror["is_mirror"] is True
        assert mirror["source_split_id"] == source_split_id

    def test_multi_split_transaction_has_unique_split_ids(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """Multiple splits in same transaction should each have unique IDs."""
        # Create second category
        cat2 = client.post("/api/v1/categories", json={"name": "Split ID Test Cat2"}).json()

        # Create transaction with multiple splits
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": "2026-01-15",
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-60.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    },
                    {
                        "amount": {"amount": "-40.00", "currency": "USD"},
                        "category_id": cat2["id"],
                    },
                ],
            },
        )
        assert response.status_code == 201
        splits = response.json()["splits"]

        # All splits have IDs
        assert all("id" in s for s in splits)
        assert all(s["id"].startswith("split_") for s in splits)

        # All IDs are unique
        split_ids = [s["id"] for s in splits]
        assert len(split_ids) == len(set(split_ids))


class TestPatchSplitModifications:
    """Tests for PATCH modification sub-cases (M1-M6)."""

    def test_m1_patch_category_split_amount_change(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """M1: PATCH changing amount on category split updates amount, preserves ID."""
        # Create transaction with -100.00 category split
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # PATCH to -150.00 with same split ID
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-150.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_id,
                        "amount": {"amount": "-150.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )

        # Assert 200, split ID preserved, amount changed
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert updated["splits"][0]["id"] == split_id
        assert Decimal(updated["amount"]["amount"]) == Decimal("-150.00")
        assert Decimal(updated["splits"][0]["amount"]["amount"]) == Decimal("-150.00")

    def test_m2_patch_transfer_split_amount_syncs_mirror(
        self, client: TestClient, test_account: JsonDict
    ) -> None:
        """M2: PATCH changing amount on transfer split syncs mirror amount."""
        # Create savings account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings M2 Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create -500.00 transfer
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-500.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # Verify initial mirror
        initial_mirror = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(initial_mirror["transactions"]) == 1
        assert Decimal(initial_mirror["transactions"][0]["amount"]["amount"]) == Decimal("500.00")

        # PATCH to -750.00 with same split ID
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-750.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_id,
                        "amount": {"amount": "-750.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        )
        assert patch_response.status_code == 200

        # Assert source amount updated
        assert Decimal(patch_response.json()["amount"]["amount"]) == Decimal("-750.00")

        # Assert mirror amount updated to +750.00 (positive)
        updated_mirror = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(updated_mirror["transactions"]) == 1
        assert Decimal(updated_mirror["transactions"][0]["amount"]["amount"]) == Decimal("750.00")

    def test_m3_patch_category_change(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """M3: PATCH changing category_id on split updates category."""
        # Create second category (cat2)
        cat2 = client.post("/api/v1/categories", json={"name": "M3 Category 2"}).json()

        # Create transaction with test_category (cat1)
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-75.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-75.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # PATCH to cat2 with same split ID
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-75.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_id,
                        "amount": {"amount": "-75.00", "currency": "USD"},
                        "category_id": cat2["id"],
                    }
                ],
            },
        )

        # Assert category_id changed, split ID preserved
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert updated["splits"][0]["id"] == split_id
        assert updated["splits"][0]["category_id"] == cat2["id"]

    def test_m4_patch_transfer_destination_change(
        self, client: TestClient, test_account: JsonDict
    ) -> None:
        """M4: PATCH changing transfer destination deletes old mirror, creates new."""
        # Create savings1 and savings2 accounts
        savings1 = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings M4 Dest1",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()
        savings2 = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings M4 Dest2",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create -500.00 transfer to savings1
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-500.00", "currency": "USD"},
                        "transfer_account_id": savings1["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # Verify mirror exists in savings1
        s1_txns = client.get(f"/api/v1/transactions?account_id={savings1['id']}").json()
        assert len(s1_txns["transactions"]) == 1

        # PATCH to transfer to savings2 with same split ID
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_id,
                        "amount": {"amount": "-500.00", "currency": "USD"},
                        "transfer_account_id": savings2["id"],
                    }
                ],
            },
        )
        assert patch_response.status_code == 200

        # Assert savings1 has 0 transactions (old mirror deleted)
        s1_txns_after = client.get(f"/api/v1/transactions?account_id={savings1['id']}").json()
        assert len(s1_txns_after["transactions"]) == 0

        # Assert savings2 has 1 mirror transaction
        s2_txns = client.get(f"/api/v1/transactions?account_id={savings2['id']}").json()
        assert len(s2_txns["transactions"]) == 1

        # Assert new mirror has correct amount and is_mirror=True
        new_mirror = s2_txns["transactions"][0]
        assert new_mirror["is_mirror"] is True
        assert Decimal(new_mirror["amount"]["amount"]) == Decimal("500.00")

    def test_m5_patch_category_to_transfer_creates_mirror(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """M5: PATCH converting category split to transfer creates mirror."""
        # Create savings account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings M5 Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create -200.00 transaction with category split
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-200.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-200.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # Verify savings has 0 transactions
        s_txns_before = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_before["transactions"]) == 0

        # PATCH split to be transfer (remove category_id, add transfer_account_id), keep split ID
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-200.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_id,
                        "amount": {"amount": "-200.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        )

        # Assert 200
        assert patch_response.status_code == 200
        updated = patch_response.json()

        # Assert split now has transfer_account_id, no category_id
        assert updated["splits"][0]["id"] == split_id
        assert updated["splits"][0]["transfer_account_id"] == savings["id"]
        assert updated["splits"][0].get("category_id") is None

        # Assert savings now has 1 mirror transaction with +200.00
        s_txns_after = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_after["transactions"]) == 1
        mirror = s_txns_after["transactions"][0]
        assert mirror["is_mirror"] is True
        assert Decimal(mirror["amount"]["amount"]) == Decimal("200.00")

    def test_m6_patch_transfer_to_category_deletes_mirror(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """M6: PATCH converting transfer split to category deletes mirror."""
        # Create savings account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings M6 Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create -300.00 transfer to savings
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-300.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-300.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # Verify mirror exists in savings
        s_txns_before = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_before["transactions"]) == 1

        # PATCH split to be category (remove transfer_account_id, add category_id), keep split ID
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-300.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_id,
                        "amount": {"amount": "-300.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )

        # Assert 200
        assert patch_response.status_code == 200
        updated = patch_response.json()

        # Assert split now has category_id, no transfer_account_id
        assert updated["splits"][0]["id"] == split_id
        assert updated["splits"][0]["category_id"] == test_category["id"]
        assert updated["splits"][0].get("transfer_account_id") is None

        # Assert savings now has 0 transactions (mirror deleted)
        s_txns_after = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_after["transactions"]) == 0


class TestPatchSplitAddRemove:
    """Tests for adding and removing splits via PATCH."""

    def test_patch_splits_no_changes_idempotent(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """PATCH with same splits and no changes is idempotent."""
        # Create transaction with -100.00 single category split
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        split_id = create_response.json()["splits"][0]["id"]

        # PATCH with exact same split (same ID, same amount, same category)
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_id,
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )

        # Assert 200, split ID unchanged, all values unchanged
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert updated["splits"][0]["id"] == split_id
        assert Decimal(updated["amount"]["amount"]) == Decimal("-100.00")
        assert Decimal(updated["splits"][0]["amount"]["amount"]) == Decimal("-100.00")
        assert updated["splits"][0]["category_id"] == test_category["id"]

    def test_patch_remove_category_split(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """PATCH removing a category split reduces split count."""
        # Create two categories
        cat2 = client.post("/api/v1/categories", json={"name": "AddRemove Cat2"}).json()

        # Create transaction with 2 splits (-60.00, -40.00 = -100.00 total)
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-60.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    },
                    {
                        "amount": {"amount": "-40.00", "currency": "USD"},
                        "category_id": cat2["id"],
                    },
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        splits = create_response.json()["splits"]
        assert len(splits) == 2

        # Get split with test_category
        split_to_keep = next(s for s in splits if s["category_id"] == test_category["id"])

        # PATCH with only 1 split (-100.00) using one of the original IDs
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split_to_keep["id"],
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )

        # Assert 200, now has 1 split, split ID preserved
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert len(updated["splits"]) == 1
        assert updated["splits"][0]["id"] == split_to_keep["id"]
        assert Decimal(updated["splits"][0]["amount"]["amount"]) == Decimal("-100.00")

    def test_patch_remove_transfer_split_deletes_mirror(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """PATCH removing transfer split deletes corresponding mirror."""
        # Create savings account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings Remove Transfer Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create transaction with 2 splits: -300.00 transfer + -200.00 category = -500.00
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-300.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    },
                    {
                        "amount": {"amount": "-200.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    },
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        splits = create_response.json()["splits"]
        assert len(splits) == 2

        # Verify savings has 1 mirror
        s_txns_before = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_before["transactions"]) == 1

        # Get the category split to keep
        category_split = next(s for s in splits if s.get("category_id") == test_category["id"])

        # PATCH to only have category split (-500.00), remove transfer split
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "id": category_split["id"],
                        "amount": {"amount": "-500.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )

        # Assert 200, now has 1 category split
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert len(updated["splits"]) == 1
        assert updated["splits"][0]["category_id"] == test_category["id"]

        # Assert savings has 0 transactions (mirror deleted)
        s_txns_after = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_after["transactions"]) == 0

    def test_patch_add_new_category_split(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """PATCH adding new category split increases split count."""
        # Create second category
        cat2 = client.post("/api/v1/categories", json={"name": "AddRemove Add Cat"}).json()

        # Create transaction with 1 split (-100.00)
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-100.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        original_split_id = create_response.json()["splits"][0]["id"]

        # PATCH with 2 splits: original split at -60.00 (with ID), new split at -40.00 (no ID)
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "id": original_split_id,
                        "amount": {"amount": "-60.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    },
                    {
                        "amount": {"amount": "-40.00", "currency": "USD"},
                        "category_id": cat2["id"],
                    },
                ],
            },
        )

        # Assert 200, now has 2 splits
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert len(updated["splits"]) == 2

        # Assert original split ID preserved
        split_ids = [s["id"] for s in updated["splits"]]
        assert original_split_id in split_ids

        # Assert new split has generated ID (split_ prefix)
        new_split = next(s for s in updated["splits"] if s["id"] != original_split_id)
        assert new_split["id"].startswith("split_")
        assert new_split["category_id"] == cat2["id"]

    def test_patch_add_new_transfer_split_creates_mirror(
        self, client: TestClient, test_account: JsonDict, test_category: JsonDict
    ) -> None:
        """PATCH adding new transfer split creates new mirror."""
        # Create savings account
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings Add Transfer Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create transaction with 1 category split (-500.00)
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-500.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        original_split_id = create_response.json()["splits"][0]["id"]

        # Verify savings has 0 transactions
        s_txns_before = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_before["transactions"]) == 0

        # PATCH to 2 splits: -300.00 transfer (no ID), -200.00 category (original ID)
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-500.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-300.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    },
                    {
                        "id": original_split_id,
                        "amount": {"amount": "-200.00", "currency": "USD"},
                        "category_id": test_category["id"],
                    },
                ],
            },
        )

        # Assert 200, now has 2 splits
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert len(updated["splits"]) == 2

        # Assert savings now has 1 mirror with +300.00
        s_txns_after = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_after["transactions"]) == 1
        mirror = s_txns_after["transactions"][0]
        assert mirror["is_mirror"] is True
        assert Decimal(mirror["amount"]["amount"]) == Decimal("300.00")

    def test_patch_mixed_update_remove_add_splits(
        self, client: TestClient, test_account: JsonDict
    ) -> None:
        """PATCH can update, remove, and add splits in single operation."""
        # Create cat1, cat2, cat3 categories and savings account
        cat1 = client.post("/api/v1/categories", json={"name": "Mixed Cat1"}).json()
        cat2 = client.post("/api/v1/categories", json={"name": "Mixed Cat2"}).json()
        cat3 = client.post("/api/v1/categories", json={"name": "Mixed Cat3"}).json()
        savings = client.post(
            "/api/v1/accounts/savings",
            json={
                "name": "Savings Mixed Test",
                "opening_balance": {"amount": "0.00", "currency": "USD"},
            },
        ).json()

        # Create transaction with 3 splits: -50.00 cat1, -30.00 cat2, -20.00 transfer = -100.00
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": test_account["id"],
                "effective_date": date.today().isoformat(),
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "amount": {"amount": "-50.00", "currency": "USD"},
                        "category_id": cat1["id"],
                    },
                    {
                        "amount": {"amount": "-30.00", "currency": "USD"},
                        "category_id": cat2["id"],
                    },
                    {
                        "amount": {"amount": "-20.00", "currency": "USD"},
                        "transfer_account_id": savings["id"],
                    },
                ],
            },
        )
        assert create_response.status_code == 201
        txn_id = create_response.json()["id"]
        splits = create_response.json()["splits"]
        assert len(splits) == 3

        # Capture split IDs
        split1 = next(s for s in splits if s.get("category_id") == cat1["id"])
        split2 = next(s for s in splits if s.get("category_id") == cat2["id"])
        split3 = next(s for s in splits if s.get("transfer_account_id") == savings["id"])

        # Verify mirror exists
        s_txns_before = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_before["transactions"]) == 1

        # PATCH with:
        # - Split 1: Updated amount to -60.00 (same ID, same cat1)
        # - Split 2: REMOVED (not included)
        # - Split 3: REMOVED (not included)
        # - New split: -40.00 cat3 (no ID)
        patch_response = client.patch(
            f"/api/v1/transactions/{txn_id}",
            json={
                "amount": {"amount": "-100.00", "currency": "USD"},
                "splits": [
                    {
                        "id": split1["id"],
                        "amount": {"amount": "-60.00", "currency": "USD"},
                        "category_id": cat1["id"],
                    },
                    {
                        "amount": {"amount": "-40.00", "currency": "USD"},
                        "category_id": cat3["id"],
                    },
                ],
            },
        )

        # Assert 200, now has 2 splits total
        assert patch_response.status_code == 200
        updated = patch_response.json()
        assert len(updated["splits"]) == 2

        # Assert split 1 ID preserved, amount changed
        updated_split1 = next(
            (s for s in updated["splits"] if s["id"] == split1["id"]), None
        )
        assert updated_split1 is not None
        assert Decimal(updated_split1["amount"]["amount"]) == Decimal("-60.00")
        assert updated_split1["category_id"] == cat1["id"]

        # Assert split 2 ID gone (cat2 split removed)
        split_ids = [s["id"] for s in updated["splits"]]
        assert split2["id"] not in split_ids

        # Assert new split has new ID with cat3
        new_split = next(
            (s for s in updated["splits"] if s["category_id"] == cat3["id"]), None
        )
        assert new_split is not None
        assert new_split["id"].startswith("split_")
        assert new_split["id"] != split1["id"]
        assert new_split["id"] != split2["id"]
        assert new_split["id"] != split3["id"]

        # Assert savings has 0 transactions (transfer mirror deleted)
        s_txns_after = client.get(f"/api/v1/transactions?account_id={savings['id']}").json()
        assert len(s_txns_after["transactions"]) == 0
