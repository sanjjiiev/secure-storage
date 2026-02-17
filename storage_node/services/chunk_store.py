"""
chunk_store.py — Local Chunk Storage Manager
===============================================
Manages encrypted chunk storage on the local filesystem.
Chunks are stored as files named by their SHA-256 hash.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ChunkStore:
    """
    Manages local filesystem storage of encrypted file chunks.

    Each chunk is stored as a separate file in the data directory,
    named by its SHA-256 hash for content-addressable retrieval.
    """

    def __init__(self, data_dir: str):
        """
        Initialize the chunk store.

        Args:
            data_dir: Directory path where chunks will be stored.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ChunkStore initialized at %s", self.data_dir)

    def _chunk_path(self, chunk_hash: str) -> Path:
        """Get the filesystem path for a chunk by its hash."""
        return self.data_dir / chunk_hash

    def store(self, chunk_hash: str, data: bytes) -> bool:
        """
        Store an encrypted chunk on disk.

        Args:
            chunk_hash: SHA-256 hash of the chunk (used as filename).
            data: Raw encrypted chunk bytes.

        Returns:
            True if stored successfully, False if already exists.
        """
        path = self._chunk_path(chunk_hash)
        if path.exists():
            logger.debug("Chunk %s already exists, skipping", chunk_hash[:16])
            return False

        # Verify the hash matches the data
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != chunk_hash:
            logger.error(
                "Hash mismatch: expected %s, got %s",
                chunk_hash[:16],
                actual_hash[:16],
            )
            raise ValueError(
                f"Chunk hash mismatch: expected {chunk_hash}, got {actual_hash}"
            )

        path.write_bytes(data)
        logger.info("Stored chunk %s (%d bytes)", chunk_hash[:16], len(data))
        return True

    def retrieve(self, chunk_hash: str) -> Optional[bytes]:
        """
        Retrieve a chunk from disk by its hash.

        Args:
            chunk_hash: SHA-256 hash of the chunk.

        Returns:
            The chunk data as bytes, or None if not found.
        """
        path = self._chunk_path(chunk_hash)
        if not path.exists():
            logger.warning("Chunk %s not found", chunk_hash[:16])
            return None

        data = path.read_bytes()
        logger.debug("Retrieved chunk %s (%d bytes)", chunk_hash[:16], len(data))
        return data

    def delete(self, chunk_hash: str) -> bool:
        """
        Delete a chunk from disk.

        Args:
            chunk_hash: SHA-256 hash of the chunk to delete.

        Returns:
            True if deleted, False if not found.
        """
        path = self._chunk_path(chunk_hash)
        if path.exists():
            path.unlink()
            logger.info("Deleted chunk %s", chunk_hash[:16])
            return True
        return False

    def exists(self, chunk_hash: str) -> bool:
        """Check if a chunk exists in the store."""
        return self._chunk_path(chunk_hash).exists()

    def list_chunks(self) -> List[str]:
        """
        List all chunk hashes stored locally.

        Returns:
            List of SHA-256 hash strings.
        """
        chunks = [f.name for f in self.data_dir.iterdir() if f.is_file()]
        return chunks

    @property
    def total_size(self) -> int:
        """Total size of all stored chunks in bytes."""
        return sum(
            f.stat().st_size for f in self.data_dir.iterdir() if f.is_file()
        )

    @property
    def chunk_count(self) -> int:
        """Number of chunks currently stored."""
        return len(self.list_chunks())
