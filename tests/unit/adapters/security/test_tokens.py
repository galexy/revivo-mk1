"""Tests for email verification token infrastructure."""

import pytest


class TestGenerateVerificationToken:
    """Tests for generate_verification_token function."""

    def test_returns_url_safe_string(self) -> None:
        """generate_verification_token returns URL-safe string."""
        from src.adapters.security.tokens import generate_verification_token

        token = generate_verification_token("test@example.com")

        # URL-safe: no special chars except - _ .
        assert all(c.isalnum() or c in "-_." for c in token)

    def test_different_emails_produce_different_tokens(self) -> None:
        """Different emails produce different tokens."""
        from src.adapters.security.tokens import generate_verification_token

        token1 = generate_verification_token("user1@example.com")
        token2 = generate_verification_token("user2@example.com")

        assert token1 != token2


class TestVerifyEmailToken:
    """Tests for verify_email_token function."""

    def test_valid_token_returns_email(self) -> None:
        """verify_email_token returns email for valid token."""
        from src.adapters.security.tokens import (
            generate_verification_token,
            verify_email_token,
        )

        email = "test@example.com"
        token = generate_verification_token(email)

        result = verify_email_token(token)

        assert result == email

    def test_invalid_token_returns_none(self) -> None:
        """verify_email_token returns None for invalid token."""
        from src.adapters.security.tokens import verify_email_token

        result = verify_email_token("invalid-token-string")

        assert result is None

    def test_tampered_token_returns_none(self) -> None:
        """verify_email_token returns None for tampered token."""
        from src.adapters.security.tokens import (
            generate_verification_token,
            verify_email_token,
        )

        token = generate_verification_token("test@example.com")
        tampered = token[:-5] + "XXXXX"

        result = verify_email_token(tampered)

        assert result is None

    def test_expired_token_returns_none(self) -> None:
        """verify_email_token returns None for expired token."""
        from src.adapters.security.tokens import (
            generate_verification_token,
            verify_email_token,
        )

        token = generate_verification_token("test@example.com")

        # Verify with 0 max_age (expired immediately)
        result = verify_email_token(token, max_age=0)

        assert result is None
