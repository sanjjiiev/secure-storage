"""
routes.py — DHT Tracker API Endpoints
=======================================
REST API for storage node registration, heartbeat, and chunk
location tracking.

Endpoints:
    POST /nodes/register     — Register a storage node
    POST /nodes/heartbeat    — Heartbeat from a node
    GET  /nodes              — List all active nodes
    POST /chunks/announce    — Announce a chunk is stored on a node
    GET  /chunks/{hash}/locations — Find nodes storing a chunk
    GET  /health             — Health check
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.routing_table import RoutingTable
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton routing table instance
routing_table = RoutingTable(stale_timeout=settings.NODE_STALE_TIMEOUT)


# ── Request / Response Models ──────────────────────────────

class RegisterRequest(BaseModel):
    """Request body for node registration."""
    node_id: str
    address: str


class HeartbeatRequest(BaseModel):
    """Request body for heartbeat."""
    node_id: str


class AnnounceRequest(BaseModel):
    """Request body for chunk announcement."""
    chunk_hash: str
    node_id: str


class NodeResponse(BaseModel):
    """Response model for node info."""
    node_id: str
    address: str
    last_seen: float
    chunk_count: int


class ChunkLocationResponse(BaseModel):
    """Response model for chunk location query."""
    chunk_hash: str
    nodes: List[NodeResponse]


# ── Endpoints ──────────────────────────────────────────────

@router.post("/nodes/register", response_model=NodeResponse)
async def register_node(request: RegisterRequest):
    """
    Register a new storage node with the DHT tracker.

    The node will be tracked and included in chunk routing decisions.
    Re-registering an existing node_id updates its address and heartbeat.
    """
    node = routing_table.register_node(request.node_id, request.address)
    logger.info("Node registered: %s at %s", request.node_id, request.address)
    return NodeResponse(**node.to_dict())


@router.post("/nodes/heartbeat")
async def heartbeat(request: HeartbeatRequest):
    """
    Receive a heartbeat from a storage node.

    Nodes must send periodic heartbeats to avoid being evicted
    from the routing table after the stale timeout.
    """
    success = routing_table.heartbeat(request.node_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Node {request.node_id} not found. Register first.",
        )
    return {"status": "ok", "node_id": request.node_id}


@router.get("/nodes", response_model=List[NodeResponse])
async def list_nodes():
    """List all active (non-stale) storage nodes."""
    nodes = routing_table.get_active_nodes()
    return [NodeResponse(**n.to_dict()) for n in nodes]


@router.post("/chunks/announce")
async def announce_chunk(request: AnnounceRequest):
    """
    Announce that a chunk is stored on a specific node.

    Called by storage nodes or the gateway after successful chunk storage.
    """
    node = routing_table.get_node(request.node_id)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node {request.node_id} not registered",
        )
    routing_table.store_chunk_location(request.chunk_hash, request.node_id)
    return {
        "status": "ok",
        "chunk_hash": request.chunk_hash,
        "node_id": request.node_id,
    }


@router.get(
    "/chunks/{chunk_hash}/locations",
    response_model=ChunkLocationResponse,
)
async def get_chunk_locations(chunk_hash: str):
    """
    Find all storage nodes that hold a copy of the specified chunk.
    """
    nodes = routing_table.get_chunk_locations(chunk_hash)
    return ChunkLocationResponse(
        chunk_hash=chunk_hash,
        nodes=[NodeResponse(**n.to_dict()) for n in nodes],
    )


@router.get("/nodes/closest")
async def get_closest_nodes(target_hash: str, k: int = 3):
    """
    Find the k closest nodes to a target hash using XOR distance.

    Used for initial chunk placement decisions.
    """
    nodes = routing_table.lookup_nodes(target_hash, k=k)
    return [NodeResponse(**n.to_dict()) for n in nodes]


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dht-tracker",
        "active_nodes": routing_table.node_count,
        "tracked_chunks": routing_table.chunk_count,
    }
