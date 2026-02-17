"""
proof.py — Proof of Retrievability (PoR)
==========================================
Implements challenge-response Proof of Retrievability.

When challenged, the storage node hashes the stored chunk data
with a random nonce to prove it actually possesses the data,
without transferring the entire chunk.
"""

import hashlib
import logging

logger = logging.getLogger(__name__)


def generate_por(chunk_data: bytes, challenge: str) -> str:
    """
    Generate a Proof of Retrievability for a stored chunk.

    The proof is computed as:
        SHA-256(chunk_data || challenge_nonce)

    This proves the node possesses the actual chunk data without
    transmitting the full chunk.

    Args:
        chunk_data: The raw chunk data stored on this node.
        challenge: A random nonce string sent by the challenger.

    Returns:
        Hex-encoded SHA-256 proof hash.
    """
    proof_input = chunk_data + challenge.encode("utf-8")
    proof = hashlib.sha256(proof_input).hexdigest()
    logger.debug(
        "Generated PoR proof for challenge '%s': %s...",
        challenge[:16],
        proof[:16],
    )
    return proof


def verify_por(
    chunk_data: bytes, challenge: str, expected_proof: str
) -> bool:
    """
    Verify a Proof of Retrievability.

    Used by the challenger to confirm the proof matches.

    Args:
        chunk_data: The chunk data (if available for local verification).
        challenge: The nonce that was sent.
        expected_proof: The proof returned by the storage node.

    Returns:
        True if the proof is valid.
    """
    computed = generate_por(chunk_data, challenge)
    is_valid = computed == expected_proof
    logger.debug("PoR verification: %s", "PASS" if is_valid else "FAIL")
    return is_valid
