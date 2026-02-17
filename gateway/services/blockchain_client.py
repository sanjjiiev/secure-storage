"""
blockchain_client.py — Ethereum Blockchain Client
=====================================================
Web3.py client for interacting with the deployed FileRegistry
and StorageProof smart contracts.

Reads contract addresses from a shared JSON config file
written by the Hardhat deployment script.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from web3 import Web3

logger = logging.getLogger(__name__)

# ── ABI Definitions ──────────────────────────────────────
# Minimal ABIs — only the functions we call from Python

FILE_REGISTRY_ABI = [
    {
        "inputs": [
            {"name": "fileId", "type": "bytes32"},
            {"name": "merkleRoot", "type": "bytes32"},
            {"name": "chunkCount", "type": "uint256"},
            {"name": "filename", "type": "string"},
        ],
        "name": "registerFile",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "fileId", "type": "bytes32"}],
        "name": "getFile",
        "outputs": [
            {"name": "merkleRoot", "type": "bytes32"},
            {"name": "chunkCount", "type": "uint256"},
            {"name": "filename", "type": "string"},
            {"name": "owner", "type": "address"},
            {"name": "timestamp", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "fileId", "type": "bytes32"},
            {"name": "root", "type": "bytes32"},
        ],
        "name": "verifyMerkleRoot",
        "outputs": [{"name": "isValid", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getFileCount",
        "outputs": [{"name": "count", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "index", "type": "uint256"}],
        "name": "getFileIdByIndex",
        "outputs": [{"name": "fileId", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
]

STORAGE_PROOF_ABI = [
    {
        "inputs": [
            {"name": "fileId", "type": "bytes32"},
            {"name": "node", "type": "address"},
            {"name": "proofHash", "type": "bytes32"},
            {"name": "isValid", "type": "bool"},
        ],
        "name": "submitProof",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "fileId", "type": "bytes32"},
            {"name": "node", "type": "address"},
        ],
        "name": "getProof",
        "outputs": [
            {"name": "proofHash", "type": "bytes32"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "isValid", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


class BlockchainClient:
    """
    Client for interacting with FileRegistry and StorageProof
    smart contracts on the local Hardhat Ethereum network.
    """

    def __init__(
        self,
        blockchain_url: str,
        contract_addresses_file: str,
        private_key: Optional[str] = None,
    ):
        """
        Initialize the blockchain client.

        Args:
            blockchain_url: URL of the Ethereum RPC endpoint.
            contract_addresses_file: Path to JSON file with deployed addresses.
            private_key: Private key for signing transactions.
                         Defaults to Hardhat account #0.
        """
        self.w3 = Web3(Web3.HTTPProvider(blockchain_url))

        # Default to Hardhat's first account private key
        self._private_key = (
            private_key
            or "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        )
        self._account = self.w3.eth.account.from_key(self._private_key)
        self._addresses_file = contract_addresses_file

        # Contract instances (lazy-loaded)
        self._file_registry = None
        self._storage_proof = None
        self._addresses = None

        logger.info(
            "BlockchainClient initialized (rpc=%s, account=%s)",
            blockchain_url,
            self._account.address,
        )

    def _load_addresses(self) -> Dict:
        """Load contract addresses from the shared JSON config."""
        if self._addresses is None:
            path = Path(self._addresses_file)
            if not path.exists():
                raise FileNotFoundError(
                    f"Contract addresses file not found: {self._addresses_file}. "
                    "Ensure the blockchain service has deployed the contracts."
                )
            with open(path) as f:
                self._addresses = json.load(f)
            logger.info("Loaded contract addresses from %s", path)
        return self._addresses

    @property
    def file_registry(self):
        """Get the FileRegistry contract instance."""
        if self._file_registry is None:
            addresses = self._load_addresses()
            self._file_registry = self.w3.eth.contract(
                address=Web3.to_checksum_address(addresses["FileRegistry"]),
                abi=FILE_REGISTRY_ABI,
            )
        return self._file_registry

    @property
    def storage_proof(self):
        """Get the StorageProof contract instance."""
        if self._storage_proof is None:
            addresses = self._load_addresses()
            self._storage_proof = self.w3.eth.contract(
                address=Web3.to_checksum_address(addresses["StorageProof"]),
                abi=STORAGE_PROOF_ABI,
            )
        return self._storage_proof

    def _send_tx(self, func):
        """Build, sign, and send a contract transaction."""
        tx = func.build_transaction(
            {
                "from": self._account.address,
                "nonce": self.w3.eth.get_transaction_count(
                    self._account.address
                ),
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )
        signed = self.w3.eth.account.sign_transaction(
            tx, self._private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Transaction mined: %s", receipt.transactionHash.hex())
        return receipt

    # ── File Registry Methods ────────────────────────────

    def register_file(
        self,
        file_id: str,
        merkle_root: str,
        chunk_count: int,
        filename: str,
    ) -> str:
        """
        Register a file's metadata on the blockchain.

        Args:
            file_id: Hex-encoded unique file identifier.
            merkle_root: Hex-encoded Merkle root hash.
            chunk_count: Number of chunks in the file.
            filename: Original filename.

        Returns:
            Transaction hash as hex string.
        """
        file_id_bytes = bytes.fromhex(file_id.replace("0x", "").zfill(64))
        root_bytes = bytes.fromhex(merkle_root.replace("0x", "").zfill(64))

        func = self.file_registry.functions.registerFile(
            file_id_bytes, root_bytes, chunk_count, filename
        )
        receipt = self._send_tx(func)
        logger.info(
            "Registered file %s on blockchain (tx=%s)",
            file_id[:16],
            receipt.transactionHash.hex(),
        )
        return receipt.transactionHash.hex()

    def get_file_metadata(self, file_id: str) -> Dict:
        """
        Retrieve file metadata from the blockchain.

        Args:
            file_id: Hex-encoded file identifier.

        Returns:
            Dictionary with file metadata.
        """
        file_id_bytes = bytes.fromhex(file_id.replace("0x", "").zfill(64))
        result = self.file_registry.functions.getFile(file_id_bytes).call()

        return {
            "merkle_root": result[0].hex(),
            "chunk_count": result[1],
            "filename": result[2],
            "owner": result[3],
            "timestamp": result[4],
        }

    def verify_merkle_root(self, file_id: str, merkle_root: str) -> bool:
        """
        Verify a Merkle root against the on-chain value.

        Args:
            file_id: Hex-encoded file identifier.
            merkle_root: Hex-encoded Merkle root to verify.

        Returns:
            True if the root matches.
        """
        file_id_bytes = bytes.fromhex(file_id.replace("0x", "").zfill(64))
        root_bytes = bytes.fromhex(merkle_root.replace("0x", "").zfill(64))

        return self.file_registry.functions.verifyMerkleRoot(
            file_id_bytes, root_bytes
        ).call()

    def get_file_count(self) -> int:
        """Get total number of registered files."""
        return self.file_registry.functions.getFileCount().call()

    # ── Storage Proof Methods ────────────────────────────

    def submit_storage_proof(
        self,
        file_id: str,
        node_address: str,
        proof_hash: str,
        is_valid: bool,
    ) -> str:
        """
        Submit a Proof of Retrievability result on-chain.

        Args:
            file_id: Hex-encoded file identifier.
            node_address: Ethereum address of the storage node.
            proof_hash: Hex-encoded proof hash.
            is_valid: Whether the proof was verified as valid.

        Returns:
            Transaction hash.
        """
        file_id_bytes = bytes.fromhex(file_id.replace("0x", "").zfill(64))
        proof_bytes = bytes.fromhex(proof_hash.replace("0x", "").zfill(64))

        func = self.storage_proof.functions.submitProof(
            file_id_bytes,
            Web3.to_checksum_address(node_address),
            proof_bytes,
            is_valid,
        )
        receipt = self._send_tx(func)
        return receipt.transactionHash.hex()

    def is_connected(self) -> bool:
        """Check if connected to the blockchain."""
        try:
            return self.w3.is_connected()
        except Exception:
            return False
