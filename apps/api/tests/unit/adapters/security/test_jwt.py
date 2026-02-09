"""Tests for JWT token infrastructure."""

from datetime import timedelta

import pytest


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    def test_creates_valid_jwt_string(self) -> None:
        """create_access_token returns a JWT string with three parts."""
        from src.adapters.security.jwt import create_access_token

        token = create_access_token("user_123", "hh_456")

        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature

    def test_includes_user_id_in_sub_claim(self) -> None:
        """create_access_token includes user_id as 'sub' claim."""
        from src.adapters.security.jwt import create_access_token, decode_access_token

        token = create_access_token("user_123", "hh_456")
        payload = decode_access_token(token)

        assert payload["sub"] == "user_123"

    def test_includes_household_id_claim(self) -> None:
        """create_access_token includes household_id claim."""
        from src.adapters.security.jwt import create_access_token, decode_access_token

        token = create_access_token("user_123", "hh_456")
        payload = decode_access_token(token)

        assert payload["household_id"] == "hh_456"

    def test_includes_exp_and_iat_claims(self) -> None:
        """create_access_token includes expiration and issued-at claims."""
        from src.adapters.security.jwt import create_access_token, decode_access_token

        token = create_access_token("user_123", "hh_456")
        payload = decode_access_token(token)

        assert "exp" in payload
        assert "iat" in payload


class TestDecodeAccessToken:
    """Tests for decode_access_token function."""

    def test_decodes_valid_token(self) -> None:
        """decode_access_token returns payload for valid token."""
        from src.adapters.security.jwt import create_access_token, decode_access_token

        token = create_access_token("user_123", "hh_456")
        payload = decode_access_token(token)

        assert payload["sub"] == "user_123"
        assert payload["household_id"] == "hh_456"

    def test_raises_token_error_for_invalid_token(self) -> None:
        """decode_access_token raises TokenError for invalid token."""
        from src.adapters.security.jwt import TokenError, decode_access_token

        with pytest.raises(TokenError, match="Invalid token"):
            decode_access_token("not.a.valid.token")

    def test_raises_token_error_for_expired_token(self) -> None:
        """decode_access_token raises TokenError for expired token."""
        from src.adapters.security.jwt import (
            TokenError,
            create_access_token,
            decode_access_token,
        )

        # Create token that expires immediately
        token = create_access_token(
            "user_123", "hh_456", expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(TokenError, match="expired"):
            decode_access_token(token)

    def test_raises_token_error_for_tampered_token(self) -> None:
        """decode_access_token raises TokenError for tampered signature."""
        from src.adapters.security.jwt import (
            TokenError,
            create_access_token,
            decode_access_token,
        )

        token = create_access_token("user_123", "hh_456")
        # Tamper with signature
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(TokenError):
            decode_access_token(tampered)
