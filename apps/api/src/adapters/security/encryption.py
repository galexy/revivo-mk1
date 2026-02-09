"""Field-level AES-256-GCM encryption for sensitive data."""

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class FieldEncryption:
    """
    AES-256-GCM encryption for sensitive database fields.

    Usage:
        encryptor = FieldEncryption.from_docker_secret()
        encrypted = encryptor.encrypt("sensitive_data")
        decrypted = encryptor.decrypt(encrypted)
    """

    def __init__(self, key: bytes) -> None:
        """
        Initialize with 32-byte key for AES-256.

        Args:
            key: 32-byte encryption key

        Raises:
            ValueError: If key is not 32 bytes
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        self._aesgcm = AESGCM(key)

    @classmethod
    def generate_key(cls) -> bytes:
        """
        Generate a new encryption key.

        Returns:
            32-byte key suitable for AES-256

        Note:
            Store this key securely! Loss of key = loss of encrypted data.
        """
        return AESGCM.generate_key(bit_length=256)

    @classmethod
    def from_docker_secret(
        cls,
        secret_name: str = "encryption_key",
        secrets_dir: str = "/run/secrets",
    ) -> "FieldEncryption":
        """
        Load encryption key from Docker secret.

        Args:
            secret_name: Name of the secret file
            secrets_dir: Directory where Docker mounts secrets

        Returns:
            FieldEncryption instance

        Raises:
            FileNotFoundError: If secret file doesn't exist
            ValueError: If key is invalid
        """
        secret_path = Path(secrets_dir) / secret_name
        if not secret_path.exists():
            # Fall back to environment variable for development
            env_key = os.getenv("ENCRYPTION_KEY")
            if env_key:
                key = base64.b64decode(env_key)
                return cls(key)
            raise FileNotFoundError(
                f"Secret not found at {secret_path} and ENCRYPTION_KEY env var not set"
            )

        key = secret_path.read_bytes().strip()
        # Key might be base64 encoded in the secret file
        if len(key) == 44:  # Base64 encoded 32 bytes
            key = base64.b64decode(key)
        return cls(key)

    @classmethod
    def from_env(cls) -> "FieldEncryption":
        """
        Load encryption key from environment variable.
        For development/testing only.

        Returns:
            FieldEncryption instance

        Raises:
            ValueError: If ENCRYPTION_KEY not set or invalid
        """
        env_key = os.getenv("ENCRYPTION_KEY")
        if not env_key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        key = base64.b64decode(env_key)
        return cls(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded nonce+ciphertext
        """
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Prepend nonce to ciphertext for storage
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted: Base64-encoded nonce+ciphertext from encrypt()

        Returns:
            Original plaintext

        Raises:
            cryptography.exceptions.InvalidTag: If decryption fails
        """
        data = base64.b64decode(encrypted)
        nonce = data[:12]
        ciphertext = data[12:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
