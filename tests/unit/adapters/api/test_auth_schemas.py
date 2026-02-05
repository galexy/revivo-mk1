"""Tests for auth request/response schemas.

Validates password complexity rules, email format validation,
and display_name requirements for RegisterRequest.
"""

import pytest
from pydantic import ValidationError


class TestRegisterRequestPasswordValidation:
    """Tests for RegisterRequest password complexity rules."""

    def test_valid_password_accepted(self) -> None:
        """Valid password passes validation."""
        from src.adapters.api.schemas.auth import RegisterRequest

        req = RegisterRequest(
            email="test@example.com",
            password="ValidPass123!",
            display_name="Test",
        )
        assert req.password == "ValidPass123!"

    def test_password_too_short_rejected(self) -> None:
        """Password under 8 chars is rejected."""
        from src.adapters.api.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError, match="8 characters"):
            RegisterRequest(
                email="test@example.com",
                password="Ab1!",
                display_name="Test",
            )

    def test_password_no_uppercase_rejected(self) -> None:
        """Password without uppercase is rejected."""
        from src.adapters.api.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError, match="uppercase"):
            RegisterRequest(
                email="test@example.com",
                password="alllowercase1!",
                display_name="Test",
            )

    def test_password_no_lowercase_rejected(self) -> None:
        """Password without lowercase is rejected."""
        from src.adapters.api.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError, match="lowercase"):
            RegisterRequest(
                email="test@example.com",
                password="ALLUPPERCASE1!",
                display_name="Test",
            )

    def test_password_no_number_rejected(self) -> None:
        """Password without number is rejected."""
        from src.adapters.api.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError, match="number"):
            RegisterRequest(
                email="test@example.com",
                password="NoNumbers!!",
                display_name="Test",
            )

    def test_password_no_symbol_rejected(self) -> None:
        """Password without symbol is rejected."""
        from src.adapters.api.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError, match="symbol"):
            RegisterRequest(
                email="test@example.com",
                password="NoSymbol123",
                display_name="Test",
            )

    def test_invalid_email_rejected(self) -> None:
        """Invalid email format is rejected."""
        from src.adapters.api.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="ValidPass123!",
                display_name="Test",
            )

    def test_empty_display_name_rejected(self) -> None:
        """Empty display name is rejected."""
        from src.adapters.api.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError, match="empty"):
            RegisterRequest(
                email="test@example.com",
                password="ValidPass123!",
                display_name="   ",
            )
