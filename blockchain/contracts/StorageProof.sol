// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title StorageProof
 * @notice Records Proof of Retrievability (PoR) results on-chain.
 * @dev    Storage nodes submit proofs to demonstrate they still
 *         possess the file chunks they claim to store.
 *
 * Flow:
 *   1. Gateway sends a random challenge nonce to a storage node
 *   2. Node computes SHA-256(chunk_data || nonce) as proof
 *   3. Gateway verifies proof and submits result on-chain
 *   4. This contract records the proof for auditability
 */
contract StorageProof {
    // ── Structs ──────────────────────────────────────────

    /**
     * @notice Record of a storage proof submission
     * @param proofHash   The PoR hash submitted by the node
     * @param nodeAddress Address of the storage node
     * @param timestamp   Block timestamp of submission
     * @param isValid     Whether the proof was verified as valid
     */
    struct ProofRecord {
        bytes32 proofHash;
        address nodeAddress;
        uint256 timestamp;
        bool    isValid;
    }

    // ── State ────────────────────────────────────────────

    /// @notice Mapping: fileId => nodeAddress => latest proof
    mapping(bytes32 => mapping(address => ProofRecord)) private proofs;

    /// @notice Total number of proofs submitted
    uint256 public totalProofs;

    // ── Events ───────────────────────────────────────────

    /// @notice Emitted when a storage proof is submitted
    event ProofSubmitted(
        bytes32 indexed fileId,
        address indexed nodeAddress,
        bytes32 proofHash,
        bool    isValid,
        uint256 timestamp
    );

    // ── External Functions ───────────────────────────────

    /**
     * @notice Submit a Proof of Retrievability for a file
     * @param fileId    The file's unique identifier
     * @param node      Address/identifier of the storage node
     * @param proofHash The SHA-256 proof hash from the node
     * @param isValid   Whether the proof was verified as valid
     */
    function submitProof(
        bytes32 fileId,
        address node,
        bytes32 proofHash,
        bool    isValid
    ) external {
        require(proofHash != bytes32(0), "Proof hash cannot be empty");

        proofs[fileId][node] = ProofRecord({
            proofHash:   proofHash,
            nodeAddress: node,
            timestamp:   block.timestamp,
            isValid:     isValid
        });

        totalProofs++;

        emit ProofSubmitted(
            fileId,
            node,
            proofHash,
            isValid,
            block.timestamp
        );
    }

    /**
     * @notice Get the latest proof record for a file from a node
     * @param fileId The file's unique identifier
     * @param node   Address of the storage node
     * @return proofHash   The proof hash
     * @return timestamp   When it was submitted
     * @return isValid     Whether it was valid
     */
    function getProof(bytes32 fileId, address node)
        external
        view
        returns (
            bytes32 proofHash,
            uint256 timestamp,
            bool    isValid
        )
    {
        ProofRecord storage p = proofs[fileId][node];
        return (p.proofHash, p.timestamp, p.isValid);
    }
}
