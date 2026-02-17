"""
test_merkle.py — Unit Tests for Merkle Tree
=============================================
"""

import pytest
from gateway.core.hashing import sha256_hash
from gateway.core.merkle import MerkleTree


class TestMerkleTree:
    """Tests for the Merkle Tree implementation."""

    def _make_hashes(self, n: int) -> list:
        """Generate n sample chunk hashes."""
        return [sha256_hash(f"chunk-{i}".encode()) for i in range(n)]

    def test_single_leaf(self):
        """Tree with one leaf: root equals the leaf hash."""
        hashes = self._make_hashes(1)
        tree = MerkleTree(hashes)
        assert tree.root == hashes[0]

    def test_two_leaves(self):
        """Tree with two leaves produces a deterministic root."""
        hashes = self._make_hashes(2)
        tree = MerkleTree(hashes)
        assert tree.root is not None
        assert tree.root != hashes[0]
        assert tree.root != hashes[1]

    def test_odd_leaves_handled(self):
        """Odd number of leaves should be handled by duplication."""
        hashes = self._make_hashes(3)
        tree = MerkleTree(hashes)
        assert tree.root is not None
        assert len(tree.levels) > 1

    def test_deterministic_root(self):
        """Same hashes always produce the same root."""
        hashes = self._make_hashes(5)
        tree1 = MerkleTree(hashes)
        tree2 = MerkleTree(hashes)
        assert tree1.root == tree2.root

    def test_different_hashes_different_root(self):
        """Different input hashes produce different roots."""
        tree1 = MerkleTree(self._make_hashes(5))
        tree2 = MerkleTree(
            [sha256_hash(f"other-{i}".encode()) for i in range(5)]
        )
        assert tree1.root != tree2.root

    def test_empty_hashes_raises(self):
        """Empty hash list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot build"):
            MerkleTree([])

    def test_proof_and_verification(self):
        """Proof for each leaf should verify successfully."""
        hashes = self._make_hashes(8)
        tree = MerkleTree(hashes)

        for i in range(len(hashes)):
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(hashes[i], proof, tree.root)

    def test_proof_odd_leaves(self):
        """Proofs work correctly with odd number of leaves."""
        hashes = self._make_hashes(7)
        tree = MerkleTree(hashes)

        for i in range(len(hashes)):
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(hashes[i], proof, tree.root)

    def test_proof_wrong_hash_fails(self):
        """Proof with wrong leaf hash should fail verification."""
        hashes = self._make_hashes(4)
        tree = MerkleTree(hashes)
        proof = tree.get_proof(0)

        wrong_hash = sha256_hash(b"tampered data")
        assert not MerkleTree.verify_proof(wrong_hash, proof, tree.root)

    def test_proof_wrong_root_fails(self):
        """Proof verified against wrong root should fail."""
        hashes = self._make_hashes(4)
        tree = MerkleTree(hashes)
        proof = tree.get_proof(0)

        wrong_root = sha256_hash(b"wrong root")
        assert not MerkleTree.verify_proof(hashes[0], proof, wrong_root)

    def test_proof_index_out_of_range(self):
        """Out-of-range index should raise IndexError."""
        hashes = self._make_hashes(4)
        tree = MerkleTree(hashes)

        with pytest.raises(IndexError):
            tree.get_proof(4)
        with pytest.raises(IndexError):
            tree.get_proof(-1)

    def test_large_tree(self):
        """Build and verify a large tree (100 leaves)."""
        hashes = self._make_hashes(100)
        tree = MerkleTree(hashes)

        # Verify a sample of proofs
        for i in [0, 25, 50, 75, 99]:
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(hashes[i], proof, tree.root)
