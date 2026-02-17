// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title FileRegistry
 * @notice Stores file metadata and Merkle roots on-chain for the
 *         decentralized file storage system.
 * @dev    Only metadata is stored on-chain — actual file chunks
 *         are stored off-chain on distributed storage nodes.
 *
 * Features:
 *   - Register files with Merkle root and chunk count
 *   - Retrieve file metadata by file ID
 *   - Verify Merkle root integrity
 *   - Track file ownership
 */
contract FileRegistry {
    // ── Structs ──────────────────────────────────────────

    /**
     * @notice Metadata for a stored file
     * @param merkleRoot  Root hash of the chunk Merkle tree
     * @param chunkCount  Number of chunks the file was split into
     * @param filename    Original filename
     * @param owner       Address that registered the file
     * @param timestamp   Block timestamp when registered
     * @param exists      Whether this file has been registered
     */
    struct FileMetadata {
        bytes32 merkleRoot;
        uint256 chunkCount;
        string  filename;
        address owner;
        uint256 timestamp;
        bool    exists;
    }

    // ── State ────────────────────────────────────────────

    /// @notice Mapping from file ID to its metadata
    mapping(bytes32 => FileMetadata) private files;

    /// @notice Array of all registered file IDs for enumeration
    bytes32[] private fileIds;

    // ── Events ───────────────────────────────────────────

    /// @notice Emitted when a new file is registered
    event FileRegistered(
        bytes32 indexed fileId,
        bytes32 merkleRoot,
        uint256 chunkCount,
        string  filename,
        address indexed owner,
        uint256 timestamp
    );

    /// @notice Emitted when a file's Merkle root is verified
    event FileVerified(
        bytes32 indexed fileId,
        bool    isValid
    );

    // ── Modifiers ────────────────────────────────────────

    modifier fileNotExists(bytes32 fileId) {
        require(!files[fileId].exists, "File already registered");
        _;
    }

    modifier fileExists(bytes32 fileId) {
        require(files[fileId].exists, "File not found");
        _;
    }

    // ── External Functions ───────────────────────────────

    /**
     * @notice Register a new file with its Merkle root and metadata
     * @param fileId     Unique identifier for the file
     * @param merkleRoot Root hash of the Merkle tree built from chunk hashes
     * @param chunkCount Number of chunks the file was split into
     * @param filename   Original filename for reference
     */
    function registerFile(
        bytes32 fileId,
        bytes32 merkleRoot,
        uint256 chunkCount,
        string  calldata filename
    ) external fileNotExists(fileId) {
        require(chunkCount > 0, "Chunk count must be > 0");
        require(merkleRoot != bytes32(0), "Merkle root cannot be empty");

        files[fileId] = FileMetadata({
            merkleRoot: merkleRoot,
            chunkCount: chunkCount,
            filename:   filename,
            owner:      msg.sender,
            timestamp:  block.timestamp,
            exists:     true
        });

        fileIds.push(fileId);

        emit FileRegistered(
            fileId,
            merkleRoot,
            chunkCount,
            filename,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @notice Get the metadata for a registered file
     * @param fileId The file's unique identifier
     * @return merkleRoot  The Merkle root hash
     * @return chunkCount  Number of file chunks
     * @return filename    Original filename
     * @return owner       Address that registered the file
     * @return timestamp   Registration timestamp
     */
    function getFile(bytes32 fileId)
        external
        view
        fileExists(fileId)
        returns (
            bytes32 merkleRoot,
            uint256 chunkCount,
            string  memory filename,
            address owner,
            uint256 timestamp
        )
    {
        FileMetadata storage f = files[fileId];
        return (f.merkleRoot, f.chunkCount, f.filename, f.owner, f.timestamp);
    }

    /**
     * @notice Verify a Merkle root against the stored value
     * @param fileId The file's unique identifier
     * @param root   The Merkle root to verify
     * @return isValid True if the root matches the stored value
     */
    function verifyMerkleRoot(bytes32 fileId, bytes32 root)
        external
        fileExists(fileId)
        returns (bool isValid)
    {
        isValid = files[fileId].merkleRoot == root;
        emit FileVerified(fileId, isValid);
        return isValid;
    }

    /**
     * @notice Get the total number of registered files
     * @return count Number of files
     */
    function getFileCount() external view returns (uint256 count) {
        return fileIds.length;
    }

    /**
     * @notice Get a file ID by its index in the registry
     * @param index Zero-based index
     * @return fileId The file identifier at the given index
     */
    function getFileIdByIndex(uint256 index)
        external
        view
        returns (bytes32 fileId)
    {
        require(index < fileIds.length, "Index out of bounds");
        return fileIds[index];
    }
}
