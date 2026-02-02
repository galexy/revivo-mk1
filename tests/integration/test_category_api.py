"""Integration tests for Category API endpoints.

Tests the full HTTP request/response cycle through FastAPI TestClient,
verifying that the API layer correctly handles category CRUD operations.

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
from src.domain.model.category import SYSTEM_CATEGORY_UNCATEGORIZED


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

    # Cleanup
    metadata.drop_all(engine)
    clear_mappers()


@pytest.fixture
def client(setup_database):
    """Create test client with fresh app instance."""
    app = create_app()
    return TestClient(app)


class TestCategoryAPI:
    """Tests for /api/v1/categories endpoints."""

    def test_list_categories_creates_uncategorized(self, client):
        """GET /categories should create Uncategorized system category if missing."""
        response = client.get("/api/v1/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data

        # Should have at least Uncategorized
        names = [c["name"] for c in data["categories"]]
        assert SYSTEM_CATEGORY_UNCATEGORIZED in names

        # Verify Uncategorized is marked as system
        uncategorized = next(c for c in data["categories"] if c["name"] == SYSTEM_CATEGORY_UNCATEGORIZED)
        assert uncategorized["is_system"] is True

    def test_create_category(self, client):
        """POST /categories should create a new category."""
        response = client.post(
            "/api/v1/categories",
            json={"name": "Food & Dining", "icon": "fork-knife"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Food & Dining"
        assert data["icon"] == "fork-knife"
        assert data["is_system"] is False
        assert data["parent_id"] is None
        assert "id" in data
        assert data["id"].startswith("cat_")

    def test_create_subcategory(self, client):
        """POST /categories should create subcategory with parent."""
        # Create parent
        parent_response = client.post(
            "/api/v1/categories",
            json={"name": "Travel Expenses"},
        )
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["id"]

        # Create child
        child_response = client.post(
            "/api/v1/categories",
            json={"name": "Hotels", "parent_id": parent_id},
        )

        assert child_response.status_code == 201
        data = child_response.json()
        assert data["name"] == "Hotels"
        assert data["parent_id"] == parent_id

    def test_get_category_tree(self, client):
        """GET /categories/tree should return hierarchical structure."""
        # Create parent and children
        parent_response = client.post(
            "/api/v1/categories",
            json={"name": "Entertainment"},
        )
        parent_id = parent_response.json()["id"]

        client.post(
            "/api/v1/categories",
            json={"name": "Movies", "parent_id": parent_id},
        )
        client.post(
            "/api/v1/categories",
            json={"name": "Games", "parent_id": parent_id},
        )

        # Get tree
        response = client.get("/api/v1/categories/tree")

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

    def test_cannot_delete_system_category(self, client):
        """DELETE system category should fail."""
        # First get categories to find Uncategorized
        list_response = client.get("/api/v1/categories")
        categories = list_response.json()["categories"]
        uncategorized = next(c for c in categories if c["is_system"])

        # Try to delete
        response = client.delete(f"/api/v1/categories/{uncategorized['id']}")

        assert response.status_code == 400
        assert "CANNOT_DELETE_SYSTEM" in response.json()["detail"]["code"]

    def test_cannot_modify_system_category(self, client):
        """PATCH system category should fail."""
        # Get Uncategorized
        list_response = client.get("/api/v1/categories")
        categories = list_response.json()["categories"]
        uncategorized = next(c for c in categories if c["is_system"])

        # Try to rename
        response = client.patch(
            f"/api/v1/categories/{uncategorized['id']}",
            json={"name": "New Name"},
        )

        assert response.status_code == 400

    def test_update_category_name(self, client):
        """PATCH /categories/{id} should update name."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "Old Name"},
        )
        category_id = create_response.json()["id"]

        # Update
        response = client.patch(
            f"/api/v1/categories/{category_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_delete_category(self, client):
        """DELETE /categories/{id} should delete category."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "To Delete"},
        )
        category_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/categories/{category_id}")
        assert response.status_code == 204

        # Verify gone
        get_response = client.get(f"/api/v1/categories/{category_id}")
        assert get_response.status_code == 404

    def test_get_single_category(self, client):
        """GET /categories/{id} should return single category."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "Single Get Test"},
        )
        category_id = create_response.json()["id"]

        # Get it
        response = client.get(f"/api/v1/categories/{category_id}")

        assert response.status_code == 200
        assert response.json()["id"] == category_id
        assert response.json()["name"] == "Single Get Test"

    def test_get_nonexistent_category(self, client):
        """GET /categories/{id} returns 404 for nonexistent."""
        response = client.get("/api/v1/categories/cat_01h455vb4pex5vsknk084sn02q")
        assert response.status_code == 404
