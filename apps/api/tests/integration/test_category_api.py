"""Integration tests for Category API endpoints.

Tests the full HTTP request/response cycle through FastAPI TestClient,
verifying that the API layer correctly handles category CRUD operations
with JWT authentication and household-scoped data access.

Auth flow: register -> verify email -> login -> use JWT bearer token.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from domain.model.category import SYSTEM_CATEGORY_UNCATEGORIZED
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
    """Set up test database with fresh tables for category tests."""
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


class TestCategoryAPI:
    """Tests for /api/v1/categories endpoints."""

    def test_list_categories_creates_uncategorized(self, client, auth_headers):
        """GET /categories should create Uncategorized system category if missing."""
        response = client.get("/api/v1/categories", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data

        # Should have at least Uncategorized
        names = [c["name"] for c in data["categories"]]
        assert SYSTEM_CATEGORY_UNCATEGORIZED in names

        # Verify Uncategorized is marked as system
        uncategorized = next(
            c for c in data["categories"] if c["name"] == SYSTEM_CATEGORY_UNCATEGORIZED
        )
        assert uncategorized["is_system"] is True

    def test_create_category(self, client, auth_headers):
        """POST /categories should create a new category."""
        response = client.post(
            "/api/v1/categories",
            json={"name": "Food & Dining", "icon": "fork-knife"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Food & Dining"
        assert data["icon"] == "fork-knife"
        assert data["is_system"] is False
        assert data["parent_id"] is None
        assert "id" in data
        assert data["id"].startswith("cat_")

    def test_create_subcategory(self, client, auth_headers):
        """POST /categories should create subcategory with parent."""
        # Create parent
        parent_response = client.post(
            "/api/v1/categories",
            json={"name": "Travel Expenses"},
            headers=auth_headers,
        )
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["id"]

        # Create child
        child_response = client.post(
            "/api/v1/categories",
            json={"name": "Hotels", "parent_id": parent_id},
            headers=auth_headers,
        )

        assert child_response.status_code == 201
        data = child_response.json()
        assert data["name"] == "Hotels"
        assert data["parent_id"] == parent_id

    def test_get_category_tree(self, client, auth_headers):
        """GET /categories/tree should return hierarchical structure."""
        # Create parent and children
        parent_response = client.post(
            "/api/v1/categories",
            json={"name": "Entertainment"},
            headers=auth_headers,
        )
        parent_id = parent_response.json()["id"]

        client.post(
            "/api/v1/categories",
            json={"name": "Movies", "parent_id": parent_id},
            headers=auth_headers,
        )
        client.post(
            "/api/v1/categories",
            json={"name": "Games", "parent_id": parent_id},
            headers=auth_headers,
        )

        # Get tree
        response = client.get("/api/v1/categories/tree", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "root" in data
        assert "children" in data

        # Entertainment should be in root
        root_names = [c["name"] for c in data["root"]]
        assert "Entertainment" in root_names

        # Movies and Games should be children of Entertainment
        if parent_id in data["children"]:
            child_names = [c["name"] for c in data["children"][parent_id]]
            assert "Movies" in child_names
            assert "Games" in child_names

    def test_cannot_delete_system_category(self, client, auth_headers):
        """DELETE system category should fail."""
        # First get categories to find Uncategorized
        list_response = client.get("/api/v1/categories", headers=auth_headers)
        categories = list_response.json()["categories"]
        uncategorized = next(c for c in categories if c["is_system"])

        # Try to delete
        response = client.delete(
            f"/api/v1/categories/{uncategorized['id']}", headers=auth_headers
        )

        assert response.status_code == 400
        assert "CANNOT_DELETE_SYSTEM" in response.json()["detail"]["code"]

    def test_cannot_modify_system_category(self, client, auth_headers):
        """PATCH system category should fail."""
        # Get Uncategorized
        list_response = client.get("/api/v1/categories", headers=auth_headers)
        categories = list_response.json()["categories"]
        uncategorized = next(c for c in categories if c["is_system"])

        # Try to rename
        response = client.patch(
            f"/api/v1/categories/{uncategorized['id']}",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_update_category_name(self, client, auth_headers):
        """PATCH /categories/{id} should update name."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "Old Name"},
            headers=auth_headers,
        )
        category_id = create_response.json()["id"]

        # Update
        response = client.patch(
            f"/api/v1/categories/{category_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_delete_category(self, client, auth_headers):
        """DELETE /categories/{id} should delete category."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "To Delete"},
            headers=auth_headers,
        )
        category_id = create_response.json()["id"]

        # Delete
        response = client.delete(
            f"/api/v1/categories/{category_id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify gone
        get_response = client.get(
            f"/api/v1/categories/{category_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_get_single_category(self, client, auth_headers):
        """GET /categories/{id} should return single category."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "Single Get Test"},
            headers=auth_headers,
        )
        category_id = create_response.json()["id"]

        # Get it
        response = client.get(f"/api/v1/categories/{category_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == category_id
        assert response.json()["name"] == "Single Get Test"

    def test_get_nonexistent_category(self, client, auth_headers):
        """GET /categories/{id} returns 404 for nonexistent."""
        response = client.get(
            "/api/v1/categories/cat_01h455vb4pex5vsknk084sn02q",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCategoryType:
    """Tests for category type field."""

    def test_create_category_default_expense(self, client, auth_headers):
        """Category should default to expense type."""
        response = client.post(
            "/api/v1/categories",
            json={"name": "Groceries Default Type"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["category_type"] == "expense"

    def test_create_category_expense_explicit(self, client, auth_headers):
        """Can create category with explicit expense type."""
        response = client.post(
            "/api/v1/categories",
            json={"name": "Utilities Explicit", "category_type": "expense"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["category_type"] == "expense"

    def test_create_category_income_type(self, client, auth_headers):
        """Can create category with income type."""
        response = client.post(
            "/api/v1/categories",
            json={"name": "Salary", "category_type": "income"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["category_type"] == "income"

    def test_create_category_invalid_type_returns_422(self, client, auth_headers):
        """Invalid category type should return 422."""
        response = client.post(
            "/api/v1/categories",
            json={"name": "Test Invalid Type", "category_type": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_get_category_includes_type(self, client, auth_headers):
        """GET category should include category_type."""
        # Create
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "Utilities Get Type", "category_type": "expense"},
            headers=auth_headers,
        )
        cat_id = create_response.json()["id"]

        # Get
        get_response = client.get(f"/api/v1/categories/{cat_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["category_type"] == "expense"

    def test_list_categories_includes_type(self, client, auth_headers):
        """GET /categories list should include category_type."""
        # Create category with income type
        client.post(
            "/api/v1/categories",
            json={"name": "Interest Income", "category_type": "income"},
            headers=auth_headers,
        )

        # List all
        response = client.get("/api/v1/categories", headers=auth_headers)
        assert response.status_code == 200

        # Find the income category
        categories = response.json()["categories"]
        income_cat = next(
            (c for c in categories if c["name"] == "Interest Income"), None
        )
        assert income_cat is not None
        assert income_cat["category_type"] == "income"

    def test_category_type_persisted_through_round_trip(self, client, auth_headers):
        """Category type should persist through create -> get -> list."""
        # Create income category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "Dividends", "category_type": "income"},
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        cat_id = create_response.json()["id"]
        assert create_response.json()["category_type"] == "income"

        # Get by ID
        get_response = client.get(f"/api/v1/categories/{cat_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["category_type"] == "income"

        # List all
        list_response = client.get("/api/v1/categories", headers=auth_headers)
        categories = list_response.json()["categories"]
        dividends = next((c for c in categories if c["id"] == cat_id), None)
        assert dividends is not None
        assert dividends["category_type"] == "income"
