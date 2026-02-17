"""
dht_client.py — DHT Tracker Client
======================================
HTTP client for interacting with the DHT tracker service.
Handles node discovery, chunk location tracking, and announcement.
"""

import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class DHTClient:
    """
    Client for the DHT Tracker REST API.

    Provides methods to find storage nodes, announce chunk
    locations, and retrieve chunk location data.
    """

    def __init__(self, tracker_url: str):
        """
        Initialize the DHT client.

        Args:
            tracker_url: Base URL of the DHT tracker service.
        """
        self.tracker_url = tracker_url.rstrip("/")
        logger.info("DHTClient initialized with tracker at %s", self.tracker_url)

    async def get_active_nodes(self) -> List[Dict]:
        """
        Get all active storage nodes from the tracker.

        Returns:
            List of node info dictionaries.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.tracker_url}/nodes")
            response.raise_for_status()
            nodes = response.json()
            logger.debug("Retrieved %d active nodes", len(nodes))
            return nodes

    async def get_closest_nodes(
        self, target_hash: str, k: int = 3
    ) -> List[Dict]:
        """
        Find the k closest nodes to a target hash.

        Args:
            target_hash: The hash to find nearest nodes for.
            k: Number of nodes to return.

        Returns:
            List of node info dictionaries sorted by XOR distance.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.tracker_url}/nodes/closest",
                params={"target_hash": target_hash, "k": k},
            )
            response.raise_for_status()
            return response.json()

    async def announce_chunk(self, chunk_hash: str, node_id: str) -> None:
        """
        Announce that a chunk is stored on a specific node.

        Args:
            chunk_hash: SHA-256 hash of the chunk.
            node_id: ID of the node storing the chunk.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.tracker_url}/chunks/announce",
                json={"chunk_hash": chunk_hash, "node_id": node_id},
            )
            response.raise_for_status()
            logger.debug(
                "Announced chunk %s on node %s",
                chunk_hash[:16],
                node_id,
            )

    async def find_chunk(self, chunk_hash: str) -> List[Dict]:
        """
        Find all nodes that store a given chunk.

        Args:
            chunk_hash: SHA-256 hash of the chunk to locate.

        Returns:
            List of node info dictionaries.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.tracker_url}/chunks/{chunk_hash}/locations"
            )
            response.raise_for_status()
            data = response.json()
            return data.get("nodes", [])
