"""
test_chunker.py — Unit Tests for File Chunking
================================================
"""

import pytest
from gateway.core.chunker import split_file, reassemble_file


class TestSplitFile:
    """Tests for the split_file function."""

    def test_split_small_file(self):
        """File smaller than chunk size produces one chunk."""
        data = b"Hello, World!"
        chunks = split_file(data, chunk_size=1024)
        assert len(chunks) == 1
        assert chunks[0] == data

    def test_split_exact_multiple(self):
        """File that is exact multiple of chunk size."""
        data = b"A" * 100
        chunks = split_file(data, chunk_size=50)
        assert len(chunks) == 2
        assert all(len(c) == 50 for c in chunks)

    def test_split_with_remainder(self):
        """File that has a remainder after splitting."""
        data = b"B" * 150
        chunks = split_file(data, chunk_size=100)
        assert len(chunks) == 2
        assert len(chunks[0]) == 100
        assert len(chunks[1]) == 50

    def test_split_large_file(self):
        """Split a larger file (1 MB)."""
        data = b"X" * (1024 * 1024)
        chunks = split_file(data, chunk_size=262144)
        assert len(chunks) == 4

    def test_split_empty_raises(self):
        """Empty data should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot split empty"):
            split_file(b"")

    def test_split_invalid_chunk_size(self):
        """Zero or negative chunk size should raise ValueError."""
        with pytest.raises(ValueError, match="positive integer"):
            split_file(b"data", chunk_size=0)


class TestReassembleFile:
    """Tests for the reassemble_file function."""

    def test_reassemble_matches_original(self):
        """Reassembled file matches original data."""
        original = b"Hello " * 1000
        chunks = split_file(original, chunk_size=256)
        result = reassemble_file(chunks)
        assert result == original

    def test_reassemble_empty_raises(self):
        """Empty chunk list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot reassemble"):
            reassemble_file([])

    def test_roundtrip_binary(self):
        """Round-trip with binary data."""
        original = bytes(range(256)) * 100
        chunks = split_file(original, chunk_size=512)
        result = reassemble_file(chunks)
        assert result == original
