"""Tests for AuthService application service."""

import pytest
from unittest.mock import MagicMock, patch


class TestAuthServiceRegister:
    """Tests for AuthService.register() method."""

    def test_register_creates_user_and_household(self) -> None:
        """register() creates User and Household, returns RegistrationResult."""
        from src.application.services.auth_service import AuthService, RegistrationResult

        uow = self._make_mock_uow(existing_email=None)
        service = AuthService(uow)

        result = service.register(
            email="new@example.com",
            password="Test123!@",
            display_name="New User",
        )

        assert isinstance(result, RegistrationResult)
        assert result.user.email == "new@example.com"
        assert result.household.name == "New User's Household"
        assert result.verification_token is not None

    def test_register_normalizes_email(self) -> None:
        """register() lowercases email."""
        from src.application.services.auth_service import AuthService, RegistrationResult

        uow = self._make_mock_uow(existing_email=None)
        service = AuthService(uow)

        result = service.register(
            email="Test@EXAMPLE.COM",
            password="Test123!@",
            display_name="Test",
        )

        assert isinstance(result, RegistrationResult)
        assert result.user.email == "test@example.com"

    def test_register_duplicate_email_returns_error(self) -> None:
        """register() returns AuthError when email already exists."""
        from src.application.services.auth_service import AuthService, AuthError

        # Mock returns existing user for this email
        uow = self._make_mock_uow(existing_email="taken@example.com")
        service = AuthService(uow)

        result = service.register(
            email="taken@example.com",
            password="Test123!@",
            display_name="Test",
        )

        assert isinstance(result, AuthError)
        assert result.code == "REGISTRATION_FAILED"

    def test_register_hashes_password(self) -> None:
        """register() hashes password (does not store plaintext)."""
        from src.application.services.auth_service import AuthService, RegistrationResult

        uow = self._make_mock_uow(existing_email=None)
        service = AuthService(uow)

        result = service.register(
            email="new@example.com",
            password="Test123!@",
            display_name="Test",
        )

        assert isinstance(result, RegistrationResult)
        assert result.user.password_hash != "Test123!@"
        assert result.user.password_hash.startswith("$argon2")

    @staticmethod
    def _make_mock_uow(existing_email: str | None) -> MagicMock:
        """Create mock UnitOfWork with stubbed repositories."""
        from src.domain.model.entity_id import HouseholdId, UserId
        from src.domain.model.user import User

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
        uow.commit = MagicMock()
        uow.collect_events = MagicMock()

        return uow
