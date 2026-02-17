"""
hashing.py — SHA-256 Hashing Module
=====================================
Provides SHA-256 hashing for file chunks to ensure
data integrity throughout the storage pipeline.
"""

import hashlib
import logging

logger = logging.getLogger(__name__)


def sha256_hash(data: bytes) -> str:
    """
    Compute the SHA-256 hash of the given data.

    Args:
        data: Raw bytes to hash.

    Returns:
        Hexadecimal string of the SHA-256 digest (64 characters).

    Raises:
        TypeError: If data is not bytes.
    """
    if not isinstance(data, bytes):
        raise TypeError(f"Expected bytes, got {type(data).__name__}")

    digest = hashlib.sha256(data).hexdigest()
    logger.debug("SHA-256: %s... (%d bytes)", digest[:16], len(data))
    return digest
