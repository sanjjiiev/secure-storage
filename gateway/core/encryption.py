"""
encryption.py — AES-256 Encryption Module
===========================================
Provides AES-256-CBC encryption and decryption for file chunks.
Each encrypted chunk has a random 16-byte IV prepended.

Uses PyCryptodome for cryptographic operations.
"""

import logging
import os
from typing import Tuple

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

logger = logging.getLogger(__name__)

# AES-256 key size in bytes
KEY_SIZE = 32

# AES block size in bytes
BLOCK_SIZE = AES.block_size  # 16 bytes

# IV size in bytes
IV_SIZE = 16


def generate_key() -> bytes:
    """
    Generate a cryptographically secure random AES-256 key.

    Returns:
        32-byte random key suitable for AES-256.
    """
    key = os.urandom(KEY_SIZE)
    logger.info("Generated new AES-256 encryption key")
    return key


def encrypt_chunk(data: bytes, key: bytes) -> bytes:
    """
    Encrypt a chunk of data using AES-256-CBC.

    The output format is: [16-byte IV][encrypted data with PKCS7 padding]

    Args:
        data: Raw bytes to encrypt.
        key: 32-byte AES-256 key.

    Returns:
        Encrypted bytes with IV prepended.

    Raises:
        ValueError: If the key is not 32 bytes.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")

    # Generate a random Initialization Vector
    iv = os.urandom(IV_SIZE)

    # Create cipher and encrypt with PKCS7 padding
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(data, BLOCK_SIZE)
    encrypted = cipher.encrypt(padded_data)

    # Prepend IV to ciphertext
    result = iv + encrypted
    logger.debug(
        "Encrypted %d bytes -> %d bytes (IV + ciphertext)",
        len(data),
        len(result),
    )
    return result


def decrypt_chunk(data: bytes, key: bytes) -> bytes:
    """
    Decrypt an AES-256-CBC encrypted chunk.

    Expects input format: [16-byte IV][encrypted data with PKCS7 padding]

    Args:
        data: Encrypted bytes with IV prepended.
        key: 32-byte AES-256 key (same key used for encryption).

    Returns:
        Decrypted original bytes.

    Raises:
        ValueError: If the key is not 32 bytes or data is too short.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")
    if len(data) < IV_SIZE + BLOCK_SIZE:
        raise ValueError("Encrypted data is too short to contain IV and block")

    # Extract IV from the first 16 bytes
    iv = data[:IV_SIZE]
    ciphertext = data[IV_SIZE:]

    # Create cipher and decrypt
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = cipher.decrypt(ciphertext)

    # Remove PKCS7 padding
    plaintext = unpad(padded_plaintext, BLOCK_SIZE)
    logger.debug(
        "Decrypted %d bytes -> %d bytes", len(data), len(plaintext)
    )
    return plaintext
