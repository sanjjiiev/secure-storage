"""
routes.py — Storage Node API Endpoints
========================================
REST API for storing, retrieving, and proving chunks.

Endpoints:
    POST   /chunks              — Store a chunk
    GET    /chunks/{hash}       — Retrieve a chunk
    DELETE /chunks/{hash}       — Delete a chunk
    POST   /chunks/{hash}/prove — Respond to PoR challenge
    GET    /chunks              — List stored chunks
    GET    /health              — Health check
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from services.chunk_store import ChunkStore
from services.proof import generate_por
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the chunk store
chunk_store = ChunkStore(data_dir=settings.DATA_DIR)


# ── Request / Response Models ──────────────────────────────

class StoreChunkRequest(BaseModel):
    """Request to store a chunk (base64-encoded data)."""
    chunk_hash: str
    data: str  # Base64-encoded chunk data


class ProveRequest(BaseModel):
    """Request for Proof of Retrievability challenge."""
    challenge: str


class ChunkListResponse(BaseModel):
    """Response for listing stored chunks."""
    node_id: str
    chunks: List[str]
    total_count: int
    total_size_bytes: int


# ── Endpoints ──────────────────────────────────────────────

@router.post("/chunks")
async def store_chunk(request: StoreChunkRequest):
    """
    Store an encrypted chunk on this node.

    The chunk data is base64-encoded in the request body.
    The chunk is verified against the provided hash before storage.
    """
    import base64

    try:
        data = base64.b64decode(request.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 data: {e}")

    try:
        stored = chunk_store.store(request.chunk_hash, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "stored" if stored else "already_exists",
        "chunk_hash": request.chunk_hash,
        "size_bytes": len(data),
        "node_id": settings.NODE_ID,
    }


@router.get("/chunks/{chunk_hash}")
async def retrieve_chunk(chunk_hash: str):
    """
    Retrieve an encrypted chunk by its SHA-256 hash.

    Returns the raw chunk data as application/octet-stream.
    """
    data = chunk_store.retrieve(chunk_hash)
    if data is None:
        raise HTTPException(status_code=404, detail="Chunk not found")

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"X-Chunk-Hash": chunk_hash},
    )


@router.delete("/chunks/{chunk_hash}")
async def delete_chunk(chunk_hash: str):
    """Delete a stored chunk."""
    deleted = chunk_store.delete(chunk_hash)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return {"status": "deleted", "chunk_hash": chunk_hash}


@router.post("/chunks/{chunk_hash}/prove")
async def prove_chunk(chunk_hash: str, request: ProveRequest):
    """
    Respond to a Proof of Retrievability challenge.

    The node hashes the stored chunk with the provided challenge
    nonce and returns the proof hash, demonstrating it possesses
    the actual chunk data.
    """
    data = chunk_store.retrieve(chunk_hash)
    if data is None:
        raise HTTPException(status_code=404, detail="Chunk not found")

    proof = generate_por(data, request.challenge)
    return {
        "chunk_hash": chunk_hash,
        "challenge": request.challenge,
        "proof": proof,
        "node_id": settings.NODE_ID,
    }


@router.get("/chunks", response_model=ChunkListResponse)
async def list_chunks():
    """List all chunks stored on this node."""
    chunks = chunk_store.list_chunks()
    return ChunkListResponse(
        node_id=settings.NODE_ID,
        chunks=chunks,
        total_count=chunk_store.chunk_count,
        total_size_bytes=chunk_store.total_size,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for the storage node."""
    return {
        "status": "healthy",
        "service": "storage-node",
        "node_id": settings.NODE_ID,
        "stored_chunks": chunk_store.chunk_count,
        "total_size_bytes": chunk_store.total_size,
    }
