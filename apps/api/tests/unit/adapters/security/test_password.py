"""Tests for password hashing infrastructure."""


class TestHashPassword:
    """Tests for hash_password function."""

    def test_returns_argon2_hash(self) -> None:
        """hash_password returns an Argon2 hash string."""
        from src.adapters.security.password import hash_password

        result = hash_password("TestPassword123!")

        assert result.startswith("$argon2")

    def test_different_calls_produce_different_hashes(self) -> None:
        """hash_password produces different hashes (salted) for same input."""
        from src.adapters.security.password import hash_password

        hash1 = hash_password("SamePassword")
        hash2 = hash_password("SamePassword")

        assert hash1 != hash2  # Different salts


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_correct_password_returns_true(self) -> None:
        """verify_password returns True for correct password."""
        from src.adapters.security.password import hash_password, verify_password

        password = "MySecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_wrong_password_returns_false(self) -> None:
        """verify_password returns False for wrong password."""
        from src.adapters.security.password import hash_password, verify_password

        hashed = hash_password("CorrectPassword")

        assert verify_password("WrongPassword", hashed) is False

    def test_empty_password_returns_false(self) -> None:
        """verify_password returns False for empty password."""
        from src.adapters.security.password import hash_password, verify_password

        hashed = hash_password("RealPassword")

        assert verify_password("", hashed) is False
