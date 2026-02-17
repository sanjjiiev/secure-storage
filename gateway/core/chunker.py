"""
chunker.py — File Chunking Module
==================================
Splits files into fixed-size chunks for distributed storage
and reassembles them back into the original file.

Default chunk size: 256 KB (262144 bytes)
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Default chunk size: 256 KB
DEFAULT_CHUNK_SIZE = 262144


def split_file(data: bytes, chunk_size: int = DEFAULT_CHUNK_SIZE) -> List[bytes]:
    """
    Split a file (as bytes) into fixed-size chunks.

    Args:
        data: Raw file content as bytes.
        chunk_size: Size of each chunk in bytes (default 256 KB).

    Returns:
        List of byte chunks. The last chunk may be smaller than chunk_size.

    Raises:
        ValueError: If data is empty or chunk_size is not positive.
    """
    if not data:
        raise ValueError("Cannot split empty data")
    if chunk_size <= 0:
        raise ValueError("Chunk size must be a positive integer")

    chunks = []
    total_size = len(data)

    for offset in range(0, total_size, chunk_size):
        chunk = data[offset : offset + chunk_size]
        chunks.append(chunk)

    logger.info(
        "Split %d bytes into %d chunks (chunk_size=%d)",
        total_size,
        len(chunks),
        chunk_size,
    )
    return chunks


def reassemble_file(chunks: List[bytes]) -> bytes:
    """
    Reassemble file chunks back into the original file content.

    Args:
        chunks: Ordered list of byte chunks.

    Returns:
        The reassembled file as bytes.

    Raises:
        ValueError: If the chunks list is empty.
    """
    if not chunks:
        raise ValueError("Cannot reassemble from empty chunk list")

    data = b"".join(chunks)
    logger.info(
        "Reassembled %d chunks into %d bytes", len(chunks), len(data)
    )
    return data
