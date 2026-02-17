/**
 * FileRegistry.test.js — Contract Tests
 * ========================================
 * Tests for the FileRegistry smart contract.
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FileRegistry", function () {
    let fileRegistry;
    let owner, otherAccount;

    // Sample test data
    const fileId = ethers.keccak256(ethers.toUtf8Bytes("test-file-001"));
    const merkleRoot = ethers.keccak256(ethers.toUtf8Bytes("merkle-root-hash"));
    const chunkCount = 5;
    const filename = "test_document.pdf";

    beforeEach(async function () {
        [owner, otherAccount] = await ethers.getSigners();
        const FileRegistry = await ethers.getContractFactory("FileRegistry");
        fileRegistry = await FileRegistry.deploy();
        await fileRegistry.waitForDeployment();
    });

    describe("File Registration", function () {
        it("should register a new file", async function () {
            const tx = await fileRegistry.registerFile(
                fileId,
                merkleRoot,
                chunkCount,
                filename
            );

            // Check event emission
            await expect(tx)
                .to.emit(fileRegistry, "FileRegistered")
                .withArgs(
                    fileId,
                    merkleRoot,
                    chunkCount,
                    filename,
                    owner.address,
                    await getTimestamp(tx)
                );
        });

        it("should reject duplicate file registration", async function () {
            await fileRegistry.registerFile(fileId, merkleRoot, chunkCount, filename);

            await expect(
                fileRegistry.registerFile(fileId, merkleRoot, chunkCount, filename)
            ).to.be.revertedWith("File already registered");
        });

        it("should reject zero chunk count", async function () {
            await expect(
                fileRegistry.registerFile(fileId, merkleRoot, 0, filename)
            ).to.be.revertedWith("Chunk count must be > 0");
        });

        it("should reject empty merkle root", async function () {
            await expect(
                fileRegistry.registerFile(
                    fileId,
                    ethers.ZeroHash,
                    chunkCount,
                    filename
                )
            ).to.be.revertedWith("Merkle root cannot be empty");
        });
    });

    describe("File Retrieval", function () {
        beforeEach(async function () {
            await fileRegistry.registerFile(fileId, merkleRoot, chunkCount, filename);
        });

        it("should retrieve file metadata", async function () {
            const result = await fileRegistry.getFile(fileId);
            expect(result.merkleRoot).to.equal(merkleRoot);
            expect(result.chunkCount).to.equal(chunkCount);
            expect(result.filename).to.equal(filename);
            expect(result.owner).to.equal(owner.address);
        });

        it("should reject retrieval of non-existent file", async function () {
            const fakeId = ethers.keccak256(ethers.toUtf8Bytes("nonexistent"));
            await expect(fileRegistry.getFile(fakeId)).to.be.revertedWith(
                "File not found"
            );
        });
    });

    describe("Merkle Root Verification", function () {
        beforeEach(async function () {
            await fileRegistry.registerFile(fileId, merkleRoot, chunkCount, filename);
        });

        it("should verify correct merkle root", async function () {
            const result = await fileRegistry.verifyMerkleRoot.staticCall(
                fileId,
                merkleRoot
            );
            expect(result).to.be.true;
        });

        it("should reject incorrect merkle root", async function () {
            const wrongRoot = ethers.keccak256(ethers.toUtf8Bytes("wrong"));
            const result = await fileRegistry.verifyMerkleRoot.staticCall(
                fileId,
                wrongRoot
            );
            expect(result).to.be.false;
        });
    });

    describe("File Enumeration", function () {
        it("should track file count", async function () {
            expect(await fileRegistry.getFileCount()).to.equal(0);

            await fileRegistry.registerFile(fileId, merkleRoot, chunkCount, filename);
            expect(await fileRegistry.getFileCount()).to.equal(1);
        });

        it("should retrieve file ID by index", async function () {
            await fileRegistry.registerFile(fileId, merkleRoot, chunkCount, filename);
            const retrievedId = await fileRegistry.getFileIdByIndex(0);
            expect(retrievedId).to.equal(fileId);
        });
    });
});

describe("StorageProof", function () {
    let storageProof;
    let owner, node;

    const fileId = ethers.keccak256(ethers.toUtf8Bytes("test-file-001"));
    const proofHash = ethers.keccak256(ethers.toUtf8Bytes("proof-response"));

    beforeEach(async function () {
        [owner, node] = await ethers.getSigners();
        const StorageProof = await ethers.getContractFactory("StorageProof");
        storageProof = await StorageProof.deploy();
        await storageProof.waitForDeployment();
    });

    it("should submit a valid proof", async function () {
        const tx = await storageProof.submitProof(
            fileId,
            node.address,
            proofHash,
            true
        );
        await expect(tx)
            .to.emit(storageProof, "ProofSubmitted")
            .withArgs(
                fileId,
                node.address,
                proofHash,
                true,
                await getTimestamp(tx)
            );
    });

    it("should retrieve a submitted proof", async function () {
        await storageProof.submitProof(fileId, node.address, proofHash, true);
        const result = await storageProof.getProof(fileId, node.address);
        expect(result.proofHash).to.equal(proofHash);
        expect(result.isValid).to.be.true;
    });

    it("should reject empty proof hash", async function () {
        await expect(
            storageProof.submitProof(fileId, node.address, ethers.ZeroHash, true)
        ).to.be.revertedWith("Proof hash cannot be empty");
    });

    it("should track total proofs", async function () {
        expect(await storageProof.totalProofs()).to.equal(0);
        await storageProof.submitProof(fileId, node.address, proofHash, true);
        expect(await storageProof.totalProofs()).to.equal(1);
    });
});

// Helper: extract block timestamp from a transaction
async function getTimestamp(tx) {
    const receipt = await tx.wait();
    const block = await ethers.provider.getBlock(receipt.blockNumber);
    return block.timestamp;
}
