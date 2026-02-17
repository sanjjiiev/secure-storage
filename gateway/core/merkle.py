"""
merkle.py — Merkle Tree Implementation
========================================
Builds a Merkle Tree from a list of chunk hashes to provide
cryptographic proof of file integrity. The Merkle root is stored
on-chain; individual proofs can verify any chunk belongs to the file.

Hash function: SHA-256
Leaf nodes: SHA-256 hashes of individual chunks
Internal nodes: SHA-256( left_child || right_child )
"""

import hashlib
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def _hash_pair(left: str, right: str) -> str:
    """Hash two hex-encoded hashes together: SHA-256(left || right)."""
    combined = bytes.fromhex(left) + bytes.fromhex(right)
    return hashlib.sha256(combined).hexdigest()


class MerkleTree:
    """
    A binary Merkle Tree built from a list of data hashes.

    Attributes:
        leaves: The original leaf hashes (SHA-256 hex strings).
        root: The Merkle root hash.
        levels: All levels of the tree, from leaves (index 0) to root.
    """

    def __init__(self, hashes: List[str]):
        """
        Build a Merkle Tree from a list of SHA-256 hex-encoded hashes.

        If the number of leaves is odd, the last leaf is duplicated
        to make the tree balanced.

        Args:
            hashes: List of SHA-256 hex strings (one per chunk).

        Raises:
            ValueError: If the hash list is empty.
        """
        if not hashes:
            raise ValueError("Cannot build Merkle tree from empty hash list")

        self.leaves: List[str] = list(hashes)
        self.levels: List[List[str]] = []
        self._build_tree()

        logger.info(
            "Built Merkle tree with %d leaves, root=%s",
            len(self.leaves),
            self.root[:16] + "...",
        )

    def _build_tree(self) -> None:
        """Construct all tree levels from leaves up to root."""
        # Level 0 = leaves
        current_level = list(self.leaves)
        self.levels.append(current_level)

        # Build each successive level until we reach the root
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of nodes, duplicate the last one
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = _hash_pair(left, right)
                next_level.append(parent)
            current_level = next_level
            self.levels.append(current_level)

    @property
    def root(self) -> str:
        """Return the Merkle root hash."""
        return self.levels[-1][0]

    def get_proof(self, index: int) -> List[Tuple[str, str]]:
        """
        Get the Merkle proof (authentication path) for the leaf at `index`.

        Args:
            index: Zero-based index of the leaf in the original hash list.

        Returns:
            List of (sibling_hash, direction) tuples where direction is
            'left' or 'right', indicating the sibling's position relative
            to the current node.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError(
                f"Leaf index {index} out of range [0, {len(self.leaves)})"
            )

        proof = []
        current_index = index

        for level in self.levels[:-1]:  # Skip the root level
            # Determine sibling index
            if current_index % 2 == 0:
                # Current is left child; sibling is right
                sibling_index = current_index + 1
                if sibling_index < len(level):
                    proof.append((level[sibling_index], "right"))
                else:
                    # Odd number of nodes, sibling is self (duplicated)
                    proof.append((level[current_index], "right"))
            else:
                # Current is right child; sibling is left
                sibling_index = current_index - 1
                proof.append((level[sibling_index], "left"))

            # Move up to parent index
            current_index //= 2

        return proof

    @staticmethod
    def verify_proof(
        leaf_hash: str,
        proof: List[Tuple[str, str]],
        expected_root: str,
    ) -> bool:
        """
        Verify a Merkle proof for a given leaf hash.

        Args:
            leaf_hash: The SHA-256 hash of the chunk to verify.
            proof: The authentication path from get_proof().
            expected_root: The expected Merkle root to verify against.

        Returns:
            True if the proof is valid, False otherwise.
        """
        current_hash = leaf_hash

        for sibling_hash, direction in proof:
            if direction == "left":
                current_hash = _hash_pair(sibling_hash, current_hash)
            else:
                current_hash = _hash_pair(current_hash, sibling_hash)

        is_valid = current_hash == expected_root
        logger.debug(
            "Merkle proof verification: %s (computed=%s, expected=%s)",
            "PASS" if is_valid else "FAIL",
            current_hash[:16] + "...",
            expected_root[:16] + "...",
        )
        return is_valid
