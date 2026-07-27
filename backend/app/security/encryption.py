"""Field-level encryption for sensitive personal data.

Provides symmetric Fernet encryption for PII fields (email, name, file references).
Used to add column-level encryption on top of infrastructure-level encryption at rest
(MinIO SSE + PostgreSQL disk encryption).

Personal data fields in the system:
- User.email (primary PII identifier)
- User.display_name (optional personal identifier)
- DigitalFile.file_ref (references user-uploaded content)
- Review.body (may contain personal opinions/identifiers)
- AuditLog.actor_user_id (when not anonymized)
"""

from cryptography.fernet import Fernet, InvalidToken


class FieldEncryptor:
    """Encrypts and decrypts sensitive string fields using Fernet symmetric encryption.

    Fernet guarantees that a message encrypted using it cannot be manipulated or read
    without the key. It uses AES-128-CBC with HMAC-SHA256 for authentication.

    Usage:
        encryptor = FieldEncryptor(key=settings.encryption_key)
        ciphertext = encryptor.encrypt("user@example.com")
        plaintext = encryptor.decrypt(ciphertext)
    """

    def __init__(self, key: str) -> None:
        """Initialize with a Fernet-compatible base64 key.

        Args:
            key: A URL-safe base64-encoded 32-byte key.
                 Generate with: Fernet.generate_key().decode()
        """
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string, returning a base64 ciphertext string.

        Args:
            plaintext: The sensitive value to encrypt.

        Returns:
            URL-safe base64-encoded ciphertext.
        """
        if not plaintext:
            return plaintext
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string back to plaintext.

        Args:
            ciphertext: The encrypted value (from encrypt()).

        Returns:
            The original plaintext string.

        Raises:
            InvalidToken: If the ciphertext is tampered with or the key is wrong.
        """
        if not ciphertext:
            return ciphertext
        return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key suitable for ENCRYPTION_KEY env var.

        Returns:
            A URL-safe base64-encoded 32-byte key as a string.
        """
        return Fernet.generate_key().decode("utf-8")


# Re-export InvalidToken so consumers don't need to import cryptography directly
__all__ = ["FieldEncryptor", "InvalidToken"]
