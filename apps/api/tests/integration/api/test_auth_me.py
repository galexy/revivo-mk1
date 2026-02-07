"""Integration tests for GET /auth/me endpoint.

Tests the full HTTP request/response cycle for the current user profile endpoint:
- GET /auth/me with valid JWT returns user profile with household
- GET /auth/me without JWT returns 401
- GET /auth/me with invalid JWT returns 401
- Response includes expected fields and does not leak sensitive data
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
        "postgresql://postgres:postgres@postgres:5432/finance_test",
    )


@pytest.fixture(scope="module")
def engine(database_url):
    """Create database engine for tests."""
    return create_engine(database_url, echo=False)


@pytest.fixture(scope="module")
def setup_database(engine, database_url):
    """Set up test database with fresh tables for auth/me tests."""
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
        "email": f"me_test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "display_name": "Me Test User",
    }


@pytest.fixture
def registered_verified_user(client: TestClient, test_user_data: dict) -> dict:
    """Register a test user and verify their email."""
    # Register
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 202
    user_id = response.json()["user_id"]

    # Verify email using token
    verification_token = generate_verification_token(test_user_data["email"])
    response = client.get(f"/auth/verify?token={verification_token}")
    assert response.status_code == 200

    return {**test_user_data, "user_id": user_id}


@pytest.fixture
def auth_token(client: TestClient, registered_verified_user: dict) -> str:
    """Login and return access token."""
    response = client.post(
        "/auth/token",
        data={
            "username": registered_verified_user["email"],
            "password": registered_verified_user["password"],
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuthMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    def test_get_me_returns_user_profile(
        self, client: TestClient, auth_headers: dict, registered_verified_user: dict
    ) -> None:
        """GET /auth/me with valid JWT returns complete user profile."""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check user fields
        assert "user_id" in data
        assert data["user_id"].startswith("user_")
        assert data["email"] == registered_verified_user["email"]
        assert data["display_name"] == registered_verified_user["display_name"]
        assert data["email_verified"] is True
        assert "created_at" in data

        # Check household nested object
        assert "household" in data
        household = data["household"]
        assert "id" in household
        assert household["id"].startswith("hh_")
        assert "name" in household
        assert household["is_owner"] is True  # User created their own household

        # Verify password_hash is NOT in response
        assert "password_hash" not in data
        assert "password" not in data

    def test_get_me_without_token_returns_401(self, client: TestClient) -> None:
        """GET /auth/me without Authorization header returns 401."""
        response = client.get("/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_get_me_with_invalid_token_returns_401(self, client: TestClient) -> None:
        """GET /auth/me with invalid JWT returns 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_value"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    def test_get_me_with_malformed_header_returns_401(self, client: TestClient) -> None:
        """GET /auth/me with malformed Authorization header returns 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "NotBearer token"},
        )

        assert response.status_code == 401

    def test_get_me_email_verified_reflects_user_state(
        self, client: TestClient
    ) -> None:
        """GET /auth/me reflects email_verified status accurately."""
        # Register a new user
        email = f"verify_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "display_name": "Verify Test",
            },
        )

        # Try to login before verification - should fail
        response = client.post(
            "/auth/token",
            data={"username": email, "password": password},
        )
        assert response.status_code == 401

        # Verify email
        verification_token = generate_verification_token(email)
        response = client.get(f"/auth/verify?token={verification_token}")
        assert response.status_code == 200

        # Now login should succeed
        response = client.post(
            "/auth/token",
            data={"username": email, "password": password},
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]

        # GET /auth/me should show email_verified=True
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["email_verified"] is True

    def test_get_me_household_name_format(
        self, client: TestClient, auth_headers: dict, registered_verified_user: dict
    ) -> None:
        """GET /auth/me household name follows expected format."""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Household name should be "{display_name}'s Household"
        expected_name = f"{registered_verified_user['display_name']}'s Household"
        assert data["household"]["name"] == expected_name
