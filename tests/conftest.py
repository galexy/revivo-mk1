"""Shared pytest fixtures and hypothesis configuration.

This module provides common test fixtures and configures hypothesis
for property-based testing with CI-friendly settings.

Auth fixtures provide reusable authentication context for tests:
- test_user_data: Random user credentials
- registered_user: Registered + email-verified user
- auth_tokens: Access + refresh tokens from login
- auth_headers: Authorization header dict for authenticated requests
"""

import uuid

import pytest
from decimal import Decimal
from hypothesis import settings, Verbosity

# Configure hypothesis profiles for different environments
# CI profile: More thorough testing with 200 examples
settings.register_profile("ci", max_examples=200, deadline=None)
# Dev profile: Faster feedback with 50 examples
settings.register_profile("dev", max_examples=50, deadline=None)


@pytest.fixture
def usd_100() -> "Money":
    """Create a Money instance for $100 USD."""
    from src.domain.model.money import Money

    return Money(Decimal("100.00"), "USD")


@pytest.fixture
def usd_50() -> "Money":
    """Create a Money instance for $50 USD."""
    from src.domain.model.money import Money

    return Money(Decimal("50.00"), "USD")


@pytest.fixture
def eur_100() -> "Money":
    """Create a Money instance for 100 EUR."""
    from src.domain.model.money import Money

    return Money(Decimal("100.00"), "EUR")


# --- Auth Fixtures ---


@pytest.fixture
def test_user_data() -> dict:
    """Test user credentials with unique email."""
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "display_name": "Test User",
    }


@pytest.fixture
def registered_user(client, test_user_data: dict) -> dict:
    """Register a test user and verify their email.

    Requires a `client` fixture (TestClient) in scope.
    """
    from fastapi.testclient import TestClient

    from src.adapters.security.tokens import generate_verification_token

    # Register
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 202

    # Verify email
    verification_token = generate_verification_token(test_user_data["email"])
    response = client.get(f"/auth/verify?token={verification_token}")
    assert response.status_code == 200

    return {**test_user_data, "user_id": response.json()["user_id"]}


@pytest.fixture
def auth_tokens(client, registered_user: dict) -> dict:
    """Login and return tokens.

    Requires a `client` fixture (TestClient) and `registered_user` in scope.
    """
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
