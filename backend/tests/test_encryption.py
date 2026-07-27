"""Tests for field-level encryption (Requirement 1.6).

Verifies that the FieldEncryptor provides correct encrypt/decrypt roundtrip
and handles edge cases properly.
"""

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.security.encryption import FieldEncryptor


@pytest.fixture
def encryptor() -> FieldEncryptor:
    """Create a FieldEncryptor with a fresh key for testing."""
    key = Fernet.generate_key().decode()
    return FieldEncryptor(key=key)


class TestFieldEncryptorRoundtrip:
    """Encrypt/decrypt roundtrip produces original plaintext."""

    def test_roundtrip_email(self, encryptor: FieldEncryptor) -> None:
        original = "user@example.com"
        encrypted = encryptor.encrypt(original)
        assert encryptor.decrypt(encrypted) == original

    def test_roundtrip_display_name(self, encryptor: FieldEncryptor) -> None:
        original = "María José García"
        encrypted = encryptor.encrypt(original)
        assert encryptor.decrypt(encrypted) == original

    def test_roundtrip_unicode(self, encryptor: FieldEncryptor) -> None:
        original = "ñoño@ejemplo.cl"
        encrypted = encryptor.encrypt(original)
        assert encryptor.decrypt(encrypted) == original

    def test_encrypted_differs_from_plaintext(self, encryptor: FieldEncryptor) -> None:
        original = "sensitive@data.com"
        encrypted = encryptor.encrypt(original)
        assert encrypted != original

    def test_same_plaintext_produces_different_ciphertext(self, encryptor: FieldEncryptor) -> None:
        """Fernet includes a timestamp/IV so repeated encryptions differ."""
        original = "user@example.com"
        encrypted1 = encryptor.encrypt(original)
        encrypted2 = encryptor.encrypt(original)
        assert encrypted1 != encrypted2
        # But both decrypt to the same value
        assert encryptor.decrypt(encrypted1) == original
        assert encryptor.decrypt(encrypted2) == original


class TestFieldEncryptorEdgeCases:
    """Edge cases: empty strings, wrong keys, tampered ciphertext."""

    def test_empty_string_passthrough(self, encryptor: FieldEncryptor) -> None:
        """Empty string is returned as-is (no encryption needed)."""
        assert encryptor.encrypt("") == ""
        assert encryptor.decrypt("") == ""

    def test_wrong_key_raises_invalid_token(self) -> None:
        """Decrypting with a different key raises InvalidToken."""
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()
        encryptor1 = FieldEncryptor(key=key1)
        encryptor2 = FieldEncryptor(key=key2)

        encrypted = encryptor1.encrypt("secret@email.com")
        with pytest.raises(InvalidToken):
            encryptor2.decrypt(encrypted)

    def test_tampered_ciphertext_raises_invalid_token(self, encryptor: FieldEncryptor) -> None:
        """Tampered ciphertext is detected and rejected."""
        encrypted = encryptor.encrypt("user@example.com")
        tampered = encrypted[:-5] + "XXXXX"
        with pytest.raises(Exception):
            encryptor.decrypt(tampered)


class TestFieldEncryptorKeyGeneration:
    """Key generation utility."""

    def test_generate_key_returns_valid_fernet_key(self) -> None:
        key = FieldEncryptor.generate_key()
        # Should be a valid Fernet key (url-safe base64, 32 bytes decoded)
        assert isinstance(key, str)
        # Verify it works by creating a Fernet instance
        f = Fernet(key.encode())
        assert f.encrypt(b"test") is not None

    def test_generated_keys_are_unique(self) -> None:
        key1 = FieldEncryptor.generate_key()
        key2 = FieldEncryptor.generate_key()
        assert key1 != key2


class TestFieldEncryptorWithConfig:
    """Integration with app config."""

    def test_encryptor_works_with_settings_key(self) -> None:
        """FieldEncryptor works with the key from app settings."""
        from app.config import settings

        encryptor = FieldEncryptor(key=settings.encryption_key)
        original = "test@entrelineas.cl"
        encrypted = encryptor.encrypt(original)
        assert encryptor.decrypt(encrypted) == original
