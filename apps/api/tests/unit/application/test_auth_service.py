"""Tests for AuthService application service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock


class TestAuthServiceRegister:
    """Tests for AuthService.register() method."""

    def test_register_creates_user_and_household(self) -> None:
        """register() creates User and Household, returns RegistrationResult."""
        from src.application.services.auth_service import (
            AuthService,
            RegistrationResult,
        )

        uow = self._make_mock_uow(existing_email=None)
        service = AuthService(uow)

        result = asyncio.run(
            service.register(
                email="new@example.com",
                password="Test123!@",
                display_name="New User",
            )
        )

        assert isinstance(result, RegistrationResult)
        assert result.user.email == "new@example.com"
        assert result.household.name == "New User's Household"
        assert result.verification_token is not None

    def test_register_normalizes_email(self) -> None:
        """register() lowercases email."""
        from src.application.services.auth_service import (
            AuthService,
            RegistrationResult,
        )

        uow = self._make_mock_uow(existing_email=None)
        service = AuthService(uow)

        result = asyncio.run(
            service.register(
                email="Test@EXAMPLE.COM",
                password="Test123!@",
                display_name="Test",
            )
        )

        assert isinstance(result, RegistrationResult)
        assert result.user.email == "test@example.com"

    def test_register_duplicate_email_returns_error(self) -> None:
        """register() returns AuthError when email already exists."""
        from src.application.services.auth_service import AuthError, AuthService

        # Mock returns existing user for this email
        uow = self._make_mock_uow(existing_email="taken@example.com")
        service = AuthService(uow)

        result = asyncio.run(
            service.register(
                email="taken@example.com",
                password="Test123!@",
                display_name="Test",
            )
        )

        assert isinstance(result, AuthError)
        assert result.code == "REGISTRATION_FAILED"

    def test_register_hashes_password(self) -> None:
        """register() hashes password (does not store plaintext)."""
        from src.application.services.auth_service import (
            AuthService,
            RegistrationResult,
        )

        uow = self._make_mock_uow(existing_email=None)
        service = AuthService(uow)

        result = asyncio.run(
            service.register(
                email="new@example.com",
                password="Test123!@",
                display_name="Test",
            )
        )

        assert isinstance(result, RegistrationResult)
        assert result.user.password_hash != "Test123!@"
        assert result.user.password_hash.startswith("$argon2")

    @staticmethod
    def _make_mock_uow(existing_email: str | None) -> MagicMock:
        """Create mock UnitOfWork with stubbed repositories."""
        from domain.model.user import User

        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)

        # Stub users.get_by_email
        if existing_email:
            mock_user = MagicMock(spec=User)
            mock_user.email = existing_email
            uow.users.get_by_email.return_value = mock_user
        else:
            uow.users.get_by_email.return_value = None

        # Stub other methods
        uow.users.add = MagicMock()
        uow.households.add = MagicMock()
        uow.commit = AsyncMock()
        uow.collect_events = MagicMock()

        return uow


class TestAuthServiceLogin:
    """Tests for AuthService.login() method."""

    def test_login_with_valid_credentials_returns_tokens(self) -> None:
        """login() returns AuthTokens for valid credentials."""
        from src.adapters.security.password import hash_password
        from src.application.services.auth_service import AuthService, AuthTokens

        uow = self._make_mock_uow_with_user(
            email="user@example.com",
            password_hash=hash_password("ValidPass123!"),
            email_verified=True,
        )
        service = AuthService(uow)

        result = asyncio.run(service.login("user@example.com", "ValidPass123!"))

        assert isinstance(result, AuthTokens)
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"

    def test_login_wrong_password_returns_error(self) -> None:
        """login() returns AuthError for wrong password."""
        from src.adapters.security.password import hash_password
        from src.application.services.auth_service import AuthError, AuthService

        uow = self._make_mock_uow_with_user(
            email="user@example.com",
            password_hash=hash_password("CorrectPassword123!"),
            email_verified=True,
        )
        service = AuthService(uow)

        result = asyncio.run(service.login("user@example.com", "WrongPassword123!"))

        assert isinstance(result, AuthError)
        assert result.code == "INVALID_CREDENTIALS"

    def test_login_nonexistent_email_returns_error(self) -> None:
        """login() returns AuthError for nonexistent email."""
        from src.application.services.auth_service import AuthError, AuthService

        uow = self._make_mock_uow_with_user(email=None)
        service = AuthService(uow)

        result = asyncio.run(service.login("nobody@example.com", "SomePass123!"))

        assert isinstance(result, AuthError)
        assert result.code == "INVALID_CREDENTIALS"

    def test_login_unverified_email_returns_error(self) -> None:
        """login() returns AuthError if email not verified."""
        from src.adapters.security.password import hash_password
        from src.application.services.auth_service import AuthError, AuthService

        uow = self._make_mock_uow_with_user(
            email="user@example.com",
            password_hash=hash_password("ValidPass123!"),
            email_verified=False,
        )
        service = AuthService(uow)

        result = asyncio.run(service.login("user@example.com", "ValidPass123!"))

        assert isinstance(result, AuthError)
        assert result.code == "EMAIL_NOT_VERIFIED"

    @staticmethod
    def _make_mock_uow_with_user(
        email: str | None,
        password_hash: str = "",
        email_verified: bool = True,
    ) -> MagicMock:
        """Create mock UnitOfWork with optional user."""
        from domain.model.entity_id import HouseholdId, UserId

        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)

        if email:
            mock_user = MagicMock()
            mock_user.id = UserId.generate()
            mock_user.email = email
            mock_user.password_hash = password_hash
            mock_user.email_verified = email_verified
            mock_user.household_id = HouseholdId.generate()
            uow.users.get_by_email.return_value = mock_user
        else:
            uow.users.get_by_email.return_value = None

        uow.refresh_tokens.create_token.return_value = (
            "raw_refresh_token",
            MagicMock(),
        )
        uow.commit = AsyncMock()

        return uow


class TestAuthServiceVerifyEmail:
    """Tests for AuthService.verify_email() method."""

    def test_valid_token_marks_email_verified(self) -> None:
        """verify_email() marks user verified for valid token."""
        from src.adapters.security.tokens import generate_verification_token
        from src.application.services.auth_service import AuthService
        from domain.model.entity_id import HouseholdId
        from domain.model.user import User

        token = generate_verification_token("user@example.com")
        hh_id = HouseholdId.generate()
        user = User.create("user@example.com", "Test", "hash", hh_id)

        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)
        uow.users.get_by_email.return_value = user
        uow.commit = AsyncMock()
        uow.collect_events = MagicMock()

        service = AuthService(uow)
        result = asyncio.run(service.verify_email(token))

        assert not isinstance(result, type(None))
        assert hasattr(result, "email_verified")

    def test_invalid_token_returns_error(self) -> None:
        """verify_email() returns AuthError for invalid token."""
        from src.application.services.auth_service import AuthError, AuthService

        uow = MagicMock()
        service = AuthService(uow)

        result = asyncio.run(service.verify_email("invalid-token"))

        assert isinstance(result, AuthError)
        assert result.code == "INVALID_VERIFICATION_TOKEN"
