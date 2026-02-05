"""Authentication endpoint integration tests.

Tests the full HTTP request/response cycle for auth endpoints:
- POST /auth/register (registration with enumeration protection)
- POST /auth/token (OAuth2 compatible login)
- POST /auth/refresh (token rotation via cookie)
- GET /auth/verify (email verification)
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    """Set up test database with fresh tables for auth tests."""
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
    # Register
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 202

    # Verify email using token
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


class TestRegistration:
    """Test user registration endpoint."""

    def test_register_success(self, client) -> None:
        """Registration returns 202 with user info."""
        response = client.post(
            "/auth/register",
            json={
                "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
                "password": "ValidPass123!",
                "display_name": "New User",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["message"] == "Registration successful. Please verify your email."
        assert "user_id" in data
        assert data["user_id"].startswith("user_")

    def test_register_weak_password_rejected(self, client) -> None:
        """Weak password returns 422."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "display_name": "Test",
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email_rejected(self, client) -> None:
        """Invalid email returns 422."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "ValidPass123!",
                "display_name": "Test",
            },
        )
        assert response.status_code == 422

    def test_register_duplicate_email_returns_202(
        self, client, registered_user
    ) -> None:
        """Duplicate email returns 202 (enumeration protection)."""
        response = client.post(
            "/auth/register",
            json={
                "email": registered_user["email"],
                "password": "AnotherPass123!",
                "display_name": "Another User",
            },
        )
        # Must return 202 even for duplicate email to prevent user enumeration
        assert response.status_code == 202


class TestLogin:
    """Test login (token) endpoint."""

    def test_login_success(self, client, registered_user) -> None:
        """Login returns access token and sets refresh cookie."""
        response = client.post(
            "/auth/token",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # Check refresh token cookie was set
        cookies = response.cookies
        assert "refresh_token" in cookies

    def test_login_wrong_password(self, client, registered_user) -> None:
        """Wrong password returns 401."""
        response = client.post(
            "/auth/token",
            data={
                "username": registered_user["email"],
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client) -> None:
        """Nonexistent email returns 401."""
        response = client.post(
            "/auth/token",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!",
            },
        )
        assert response.status_code == 401

    def test_login_unverified_email(self, client) -> None:
        """Unverified email returns 401."""
        # Register but do NOT verify email
        email = f"unverified_{uuid.uuid4().hex[:8]}@example.com"
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "ValidPass123!",
                "display_name": "Unverified",
            },
        )

        # Try to login without verifying
        response = client.post(
            "/auth/token",
            data={
                "username": email,
                "password": "ValidPass123!",
            },
        )
        assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh endpoint."""

    def test_refresh_success(self, client, registered_user) -> None:
        """Refresh returns new access token."""
        # First login to get refresh token cookie
        login_response = client.post(
            "/auth/token",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
        )
        assert login_response.status_code == 200

        # Now refresh using the cookie
        response = client.post("/auth/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_without_cookie(self, client) -> None:
        """Refresh without cookie returns 401."""
        # Create a fresh client with no cookies
        app = create_app()
        fresh_client = TestClient(app)
        response = fresh_client.post("/auth/refresh")
        assert response.status_code == 401


class TestEmailVerification:
    """Test email verification endpoint."""

    def test_verify_success(self, client) -> None:
        """Valid token verifies email."""
        email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "ValidPass123!",
                "display_name": "Verify Me",
            },
        )

        token = generate_verification_token(email)
        response = client.get(f"/auth/verify?token={token}")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["email"] == email

    def test_verify_invalid_token(self, client) -> None:
        """Invalid token returns 400."""
        response = client.get("/auth/verify?token=invalid-token-value")
        assert response.status_code == 400


class TestProtectedRoutes:
    """Verify that non-auth routes require valid JWT."""

    def test_accounts_requires_auth(self, client) -> None:
        """GET /api/v1/accounts without token returns 401."""
        response = client.get("/api/v1/accounts")
        assert response.status_code == 401

    def test_accounts_with_valid_token(self, client, auth_headers) -> None:
        """GET /api/v1/accounts with valid token returns 200."""
        response = client.get("/api/v1/accounts", headers=auth_headers)
        assert response.status_code == 200

    def test_accounts_with_invalid_token(self, client) -> None:
        """GET /api/v1/accounts with invalid token returns 401."""
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
