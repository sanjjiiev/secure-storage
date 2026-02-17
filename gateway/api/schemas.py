"""
schemas.py — Pydantic Request/Response Models
=================================================
Data models for the Gateway REST API.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response returned after successful file upload."""

    file_id: str
    filename: str
    encryption_key: str          # Hex-encoded AES-256 key
    merkle_root: str             # Merkle root hash
    chunk_count: int             # Number of chunks
    chunk_hashes: List[str]      # SHA-256 hashes of encrypted chunks
    replication_factor: int      # Number of replicas per chunk
    blockchain_tx: str           # Transaction hash
    message: str = "File uploaded and distributed successfully"


class FileMetadataResponse(BaseModel):
    """Response with file metadata from blockchain."""

    file_id: str
    filename: str
    merkle_root: str
    chunk_count: int
    owner: str
    timestamp: int


class FileListResponse(BaseModel):
    """Response listing all registered files."""

    total_files: int
    files: List[FileMetadataResponse]


class VerifyChunkResult(BaseModel):
    """Result of verifying a single chunk on a node."""

    chunk_hash: str
    node_id: str
    challenge: str
    proof: str
    is_valid: bool


class VerifyResponse(BaseModel):
    """Response from file integrity verification."""

    file_id: str
    merkle_root_valid: bool
    chunk_proofs: List[VerifyChunkResult]
    all_valid: bool
    message: str


class HealthResponse(BaseModel):
    """System health check response."""

    status: str
    service: str
    blockchain_connected: bool
    active_storage_nodes: int
    total_files: int
