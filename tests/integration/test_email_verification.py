"""Integration tests for email verification flow.

Tests verify:
- Registration triggers verification email job enqueue
- Verification email template renders correctly with link and expiry
- Verification link flow works end-to-end (register -> verify -> login)
- MockEmailAdapter records emails correctly for test assertions
"""

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from src.adapters.api.app import create_app
from src.adapters.persistence.orm.base import metadata
from src.adapters.persistence.orm.mappers import clear_mappers, start_mappers
from src.adapters.security.tokens import generate_verification_token
from tests.mocks.email import MockEmailAdapter


# --- Module-scoped database fixtures (same pattern as test_auth.py) ---


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
    """Set up test database with fresh tables for email verification tests."""
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
def client_with_handlers(setup_database):
    """Create test client with event handlers registered.

    Manually registers event handlers without starting the full
    lifespan (which attempts job queue worker startup). This avoids
    teardown errors from the job queue database being unavailable.
    """
    from src.application.event_bus import clear_handlers
    from src.application.handlers import register_all_handlers

    register_all_handlers()
    app = create_app()
    client = TestClient(app)
    yield client
    clear_handlers()


@pytest.fixture
def test_user_data() -> dict:
    """Test user credentials with unique email."""
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "display_name": "Test User",
    }


# --- Tests ---


class TestRegistrationEnqueuesEmail:
    """Test that registration triggers verification email job."""

    def test_registration_enqueues_verification_email(
        self, client_with_handlers, test_user_data
    ) -> None:
        """Registration should attempt to enqueue verification email job."""
        from src.adapters.jobs.tasks import send_verification_email

        original_defer_async = send_verification_email.defer_async
        mock_defer_async = AsyncMock()
        send_verification_email.defer_async = mock_defer_async

        try:
            response = client_with_handlers.post(
                "/auth/register", json=test_user_data
            )

            assert response.status_code == 202
            # Verify defer_async was called with correct keyword args
            mock_defer_async.assert_called_once()
            call_kwargs = mock_defer_async.call_args.kwargs
            assert call_kwargs["email"] == test_user_data["email"].lower()
            assert "verification_token" in call_kwargs
            assert "user_id" in call_kwargs
        finally:
            send_verification_email.defer_async = original_defer_async

    def test_registration_succeeds_when_job_queue_disabled(
        self, client_with_handlers
    ) -> None:
        """Registration succeeds even when JOB_QUEUE_ENABLED is false."""
        email = f"nojob_{uuid.uuid4().hex[:8]}@example.com"
        with patch.dict(os.environ, {"JOB_QUEUE_ENABLED": "false"}):
            response = client_with_handlers.post(
                "/auth/register",
                json={
                    "email": email,
                    "password": "TestPassword123!",
                    "display_name": "No Job User",
                },
            )
        assert response.status_code == 202


class TestVerificationEmailTemplate:
    """Test that verification email templates render correctly."""

    def test_verification_email_contains_link(self) -> None:
        """Verification email should contain the verification link."""
        from src.adapters.email import render_verification_email

        link = "http://localhost:8000/auth/verify?token=abc123"
        html, text = render_verification_email(
            recipient_name="Test User",
            verification_link=link,
            expiry_hours=48,
        )

        assert link in html
        assert link in text

    def test_verification_email_contains_expiry(self) -> None:
        """Verification email should mention 48-hour expiry."""
        from src.adapters.email import render_verification_email

        html, text = render_verification_email(
            recipient_name="Test User",
            verification_link="http://localhost:8000/auth/verify?token=abc",
            expiry_hours=48,
        )

        assert "48 hours" in html
        assert "48 hours" in text

    def test_verification_email_renders_recipient_name(self) -> None:
        """Verification email should include recipient name."""
        from src.adapters.email import render_verification_email

        html, text = render_verification_email(
            recipient_name="Alice",
            verification_link="http://localhost:8000/auth/verify?token=abc",
            expiry_hours=48,
        )

        assert "Alice" in html
        assert "Alice" in text


class TestVerificationLinkFlow:
    """Test end-to-end verification flow: register -> verify -> login."""

    def test_verification_link_verifies_user(self, client) -> None:
        """Clicking verification link should verify user and enable login."""
        email = f"verify_{uuid.uuid4().hex[:8]}@example.com"

        # Register user (disable job queue to skip defer attempt)
        with patch.dict(os.environ, {"JOB_QUEUE_ENABLED": "false"}):
            response = client.post(
                "/auth/register",
                json={
                    "email": email,
                    "password": "SecurePass123!",
                    "display_name": "Verify User",
                },
            )
            assert response.status_code == 202

        # Generate token (simulating what the job would produce)
        token = generate_verification_token(email)

        # Click verification link
        response = client.get(f"/auth/verify?token={token}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email

        # Verify user can now login (email verified)
        response = client.post(
            "/auth/token",
            data={"username": email, "password": "SecurePass123!"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_verification_is_idempotent(self, client) -> None:
        """Re-clicking verification link should not error."""
        email = f"idempotent_{uuid.uuid4().hex[:8]}@example.com"

        # Register (disable job queue to skip defer attempt)
        with patch.dict(os.environ, {"JOB_QUEUE_ENABLED": "false"}):
            client.post(
                "/auth/register",
                json={
                    "email": email,
                    "password": "SecurePass123!",
                    "display_name": "Idempotent User",
                },
            )

        token = generate_verification_token(email)

        # Verify first time
        response = client.get(f"/auth/verify?token={token}")
        assert response.status_code == 200

        # Verify second time (idempotent)
        response = client.get(f"/auth/verify?token={token}")
        assert response.status_code == 200


class TestMockEmailAdapter:
    """Test MockEmailAdapter records emails correctly."""

    def test_records_sent_email(self) -> None:
        """MockEmailAdapter should record sent emails."""
        adapter = MockEmailAdapter()
        adapter.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_content="<h1>Hello</h1>",
            text_content="Hello",
        )

        assert len(adapter.sent_emails) == 1
        email = adapter.sent_emails[0]
        assert email.to_email == "user@example.com"
        assert email.subject == "Test Subject"
        assert email.html_content == "<h1>Hello</h1>"
        assert email.text_content == "Hello"

    def test_get_last_email(self) -> None:
        """get_last_email returns most recent email."""
        adapter = MockEmailAdapter()
        adapter.send_email("a@b.c", "First", "<p>1</p>", "1")
        adapter.send_email("d@e.f", "Second", "<p>2</p>", "2")

        last = adapter.get_last_email()
        assert last is not None
        assert last.subject == "Second"

    def test_get_last_email_empty(self) -> None:
        """get_last_email returns None when no emails sent."""
        adapter = MockEmailAdapter()
        assert adapter.get_last_email() is None

    def test_get_emails_to_filters(self) -> None:
        """get_emails_to returns only emails to specific address."""
        adapter = MockEmailAdapter()
        adapter.send_email("a@b.c", "To A", "<p>A</p>", "A")
        adapter.send_email("d@e.f", "To D", "<p>D</p>", "D")
        adapter.send_email("a@b.c", "To A again", "<p>A2</p>", "A2")

        emails_to_a = adapter.get_emails_to("a@b.c")
        assert len(emails_to_a) == 2
        assert all(e.to_email == "a@b.c" for e in emails_to_a)

    def test_clear_removes_all(self) -> None:
        """clear removes all recorded emails."""
        adapter = MockEmailAdapter()
        adapter.send_email("a@b.c", "Test", "<p>T</p>", "T")
        assert len(adapter.sent_emails) == 1

        adapter.clear()
        assert len(adapter.sent_emails) == 0
        assert adapter.get_last_email() is None
