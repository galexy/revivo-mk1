"""Integration tests for field-level encryption."""

import base64

import pytest
from cryptography.exceptions import InvalidTag

from src.adapters.security.encryption import FieldEncryption


class TestFieldEncryptionRoundTrip:
    """Test encryption round-trip scenarios."""

    def test_encrypt_decrypt_simple_string(self, field_encryption):
        """Basic encrypt/decrypt works."""
        plaintext = "my_secret_token"
        encrypted = field_encryption.encrypt(plaintext)
        decrypted = field_encryption.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_unicode(self, field_encryption):
        """Unicode characters preserved through encryption."""
        plaintext = "secret with emoji \U0001f512"
        encrypted = field_encryption.encrypt(plaintext)
        decrypted = field_encryption.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_empty_string(self, field_encryption):
        """Empty strings can be encrypted."""
        plaintext = ""
        encrypted = field_encryption.encrypt(plaintext)
        decrypted = field_encryption.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_long_string(self, field_encryption):
        """Long strings (like JWTs) work."""
        plaintext = "a" * 10000  # 10KB string
        encrypted = field_encryption.encrypt(plaintext)
        decrypted = field_encryption.decrypt(encrypted)
        assert decrypted == plaintext

    def test_same_plaintext_produces_different_ciphertext(self, field_encryption):
        """
        Each encryption uses random nonce.
        Same plaintext should produce different ciphertext.
        """
        plaintext = "repeated_secret"
        encrypted1 = field_encryption.encrypt(plaintext)
        encrypted2 = field_encryption.encrypt(plaintext)

        # Different ciphertext
        assert encrypted1 != encrypted2

        # But both decrypt to same plaintext
        assert field_encryption.decrypt(encrypted1) == plaintext
        assert field_encryption.decrypt(encrypted2) == plaintext


class TestFieldEncryptionSecurity:
    """Test encryption security properties."""

    def test_ciphertext_not_equal_to_plaintext(self, field_encryption):
        """Encrypted value is not the plaintext."""
        plaintext = "obvious_secret"
        encrypted = field_encryption.encrypt(plaintext)
        assert encrypted != plaintext
        assert plaintext not in encrypted

    def test_different_keys_cannot_decrypt(self, field_encryption):
        """Data encrypted with one key cannot be decrypted with another."""
        plaintext = "secret_data"
        encrypted = field_encryption.encrypt(plaintext)

        # Create new encryptor with different key
        different_key = FieldEncryption.generate_key()
        different_encryptor = FieldEncryption(different_key)

        with pytest.raises(InvalidTag):
            different_encryptor.decrypt(encrypted)

    def test_tampered_ciphertext_fails(self, field_encryption):
        """Modified ciphertext fails authentication."""
        plaintext = "authentic_data"
        encrypted = field_encryption.encrypt(plaintext)

        # Tamper with the ciphertext
        encrypted_bytes = base64.b64decode(encrypted)
        tampered = encrypted_bytes[:-1] + bytes([encrypted_bytes[-1] ^ 1])
        tampered_encoded = base64.b64encode(tampered).decode()

        with pytest.raises(InvalidTag):
            field_encryption.decrypt(tampered_encoded)


class TestFieldEncryptionKeyLoading:
    """Test key loading from various sources."""

    def test_load_from_environment_variable(self, env_encryption_key):
        """Key can be loaded from environment."""
        encryptor = FieldEncryption.from_env()

        plaintext = "env_secret"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_invalid_key_length_raises(self):
        """Key must be exactly 32 bytes."""
        with pytest.raises(ValueError, match="32 bytes"):
            FieldEncryption(b"too_short")

        with pytest.raises(ValueError, match="32 bytes"):
            FieldEncryption(b"x" * 64)  # Too long

    def test_generate_key_produces_valid_key(self):
        """Generated key is correct length."""
        key = FieldEncryption.generate_key()
        assert len(key) == 32

        # Can be used to create encryptor
        encryptor = FieldEncryption(key)
        encrypted = encryptor.encrypt("test")
        assert encryptor.decrypt(encrypted) == "test"


class TestFieldEncryptionBase64:
    """Test base64 encoding of encrypted values."""

    def test_encrypted_value_is_valid_base64(self, field_encryption):
        """Encrypted values can be stored as text."""
        plaintext = "base64_test"
        encrypted = field_encryption.encrypt(plaintext)

        # Should be valid base64
        decoded = base64.b64decode(encrypted)
        assert len(decoded) > 0

    def test_encrypted_value_is_ascii_safe(self, field_encryption):
        """Encrypted values contain only ASCII characters."""
        plaintext = "ascii_test"
        encrypted = field_encryption.encrypt(plaintext)

        # Should be ASCII-safe for database storage
        encrypted.encode("ascii")  # Should not raise
