"""
test_encryption.py — Unit Tests for AES-256 Encryption
========================================================
"""

import pytest
from gateway.core.encryption import (
    encrypt_chunk,
    decrypt_chunk,
    generate_key,
    KEY_SIZE,
    IV_SIZE,
)


class TestKeyGeneration:
    """Tests for key generation."""

    def test_key_length(self):
        """Generated key should be 32 bytes (AES-256)."""
        key = generate_key()
        assert len(key) == KEY_SIZE

    def test_keys_are_unique(self):
        """Each generated key should be different."""
        keys = {generate_key() for _ in range(100)}
        assert len(keys) == 100


class TestEncryption:
    """Tests for encrypt and decrypt operations."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted data can be decrypted back to original."""
        key = generate_key()
        original = b"This is confidential data!"
        encrypted = encrypt_chunk(original, key)
        decrypted = decrypt_chunk(encrypted, key)
        assert decrypted == original

    def test_encrypted_output_is_different(self):
        """Encrypted data should not match original."""
        key = generate_key()
        original = b"Sensitive information"
        encrypted = encrypt_chunk(original, key)
        assert encrypted != original

    def test_iv_is_prepended(self):
        """Encrypted output should be at least IV_SIZE + block longer."""
        key = generate_key()
        original = b"test"
        encrypted = encrypt_chunk(original, key)
        assert len(encrypted) >= IV_SIZE + 16  # IV + at least one block

    def test_different_iv_each_time(self):
        """Each encryption should use a different random IV."""
        key = generate_key()
        original = b"same plaintext"
        enc1 = encrypt_chunk(original, key)
        enc2 = encrypt_chunk(original, key)
        # IVs (first 16 bytes) should differ
        assert enc1[:IV_SIZE] != enc2[:IV_SIZE]

    def test_wrong_key_fails(self):
        """Decryption with wrong key should fail."""
        key1 = generate_key()
        key2 = generate_key()
        original = b"secret data"
        encrypted = encrypt_chunk(original, key1)
        with pytest.raises(Exception):
            decrypt_chunk(encrypted, key2)

    def test_invalid_key_length(self):
        """Key of wrong length should raise ValueError."""
        with pytest.raises(ValueError, match="Key must be"):
            encrypt_chunk(b"data", b"short_key")

    def test_large_data_roundtrip(self):
        """Encrypt/decrypt 1 MB of data."""
        key = generate_key()
        original = bytes(range(256)) * 4096  # ~1 MB
        encrypted = encrypt_chunk(original, key)
        decrypted = decrypt_chunk(encrypted, key)
        assert decrypted == original

    def test_empty_data(self):
        """Encrypting empty data should work."""
        key = generate_key()
        encrypted = encrypt_chunk(b"", key)
        decrypted = decrypt_chunk(encrypted, key)
        assert decrypted == b""
