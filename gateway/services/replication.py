"""
replication.py — Replication Manager
========================================
Manages chunk replication across storage nodes to ensure
fault tolerance. Each chunk is stored on at least k nodes.

Strategy:
    1. For each chunk, find the k closest nodes via DHT
    2. Upload chunk to all k nodes
    3. Announce chunk locations to DHT tracker
    4. Periodically verify replication factor
    5. Re-replicate if nodes go offline
"""

import base64
import logging
from typing import Dict, List, Tuple

import httpx

from services.dht_client import DHTClient

logger = logging.getLogger(__name__)


class ReplicationManager:
    """
    Manages k-replica replication of encrypted chunks across
    the storage node network.
    """

    def __init__(self, dht_client: DHTClient, replication_factor: int = 3):
        """
        Initialize the replication manager.

        Args:
            dht_client: Client for DHT tracker interactions.
            replication_factor: Number of replicas per chunk (k).
        """
        self.dht = dht_client
        self.k = replication_factor
        logger.info(
            "ReplicationManager initialized (k=%d)", self.k
        )

    async def replicate_chunk(
        self, chunk_hash: str, data: bytes
    ) -> List[str]:
        """
        Distribute a chunk to k storage nodes.

        Args:
            chunk_hash: SHA-256 hash of the encrypted chunk.
            data: The encrypted chunk data.

        Returns:
            List of node IDs that successfully stored the chunk.

        Raises:
            RuntimeError: If no nodes could store the chunk.
        """
        # Get available nodes from DHT
        nodes = await self.dht.get_active_nodes()

        if not nodes:
            raise RuntimeError("No active storage nodes available")

        # Try to store on up to k nodes
        successful_nodes = []
        encoded_data = base64.b64encode(data).decode("utf-8")

        for node in nodes[: self.k]:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{node['address']}/chunks",
                        json={
                            "chunk_hash": chunk_hash,
                            "data": encoded_data,
                        },
                    )
                    response.raise_for_status()

                    # Announce to DHT
                    await self.dht.announce_chunk(
                        chunk_hash, node["node_id"]
                    )
                    successful_nodes.append(node["node_id"])
                    logger.info(
                        "Replicated chunk %s to node %s",
                        chunk_hash[:16],
                        node["node_id"],
                    )
            except Exception as e:
                logger.warning(
                    "Failed to replicate chunk %s to node %s: %s",
                    chunk_hash[:16],
                    node.get("node_id", "unknown"),
                    e,
                )

        if not successful_nodes:
            raise RuntimeError(
                f"Failed to replicate chunk {chunk_hash} to any node"
            )

        logger.info(
            "Chunk %s replicated to %d/%d nodes",
            chunk_hash[:16],
            len(successful_nodes),
            self.k,
        )
        return successful_nodes

    async def check_replication(self, chunk_hash: str) -> Tuple[int, bool]:
        """
        Check the current replication factor for a chunk.

        Args:
            chunk_hash: SHA-256 hash of the chunk.

        Returns:
            Tuple of (current_replicas, meets_threshold).
        """
        nodes = await self.dht.find_chunk(chunk_hash)
        current = len(nodes)
        meets = current >= self.k
        logger.debug(
            "Chunk %s replication: %d/%d (%s)",
            chunk_hash[:16],
            current,
            self.k,
            "OK" if meets else "BELOW",
        )
        return current, meets

    async def repair_replication(
        self, chunk_hash: str, data: bytes
    ) -> List[str]:
        """
        Repair replication for a chunk that is below the threshold.

        Finds additional nodes and replicates the chunk to them.

        Args:
            chunk_hash: SHA-256 hash of the chunk.
            data: The encrypted chunk data.

        Returns:
            List of newly added node IDs.
        """
        current_nodes = await self.dht.find_chunk(chunk_hash)
        current_ids = {n["node_id"] for n in current_nodes}
        needed = self.k - len(current_ids)

        if needed <= 0:
            logger.debug("Chunk %s replication is sufficient", chunk_hash[:16])
            return []

        # Get all nodes and find ones that don't have this chunk
        all_nodes = await self.dht.get_active_nodes()
        candidate_nodes = [
            n for n in all_nodes if n["node_id"] not in current_ids
        ]

        new_nodes = []
        encoded_data = base64.b64encode(data).decode("utf-8")

        for node in candidate_nodes[:needed]:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{node['address']}/chunks",
                        json={
                            "chunk_hash": chunk_hash,
                            "data": encoded_data,
                        },
                    )
                    response.raise_for_status()
                    await self.dht.announce_chunk(
                        chunk_hash, node["node_id"]
                    )
                    new_nodes.append(node["node_id"])
                    logger.info(
                        "Repaired: replicated chunk %s to node %s",
                        chunk_hash[:16],
                        node["node_id"],
                    )
            except Exception as e:
                logger.warning(
                    "Failed repair replication to node %s: %s",
                    node.get("node_id", "unknown"),
                    e,
                )

        return new_nodes
