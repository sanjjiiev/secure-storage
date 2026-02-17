"""
routing_table.py — Kademlia-Style DHT Routing Table
=====================================================
Implements a distributed hash table using XOR distance metric
for peer discovery and chunk location tracking.

Node IDs and chunk hashes are treated as 256-bit integers for
XOR distance computation. Nodes are organized in k-buckets
based on their XOR distance from the tracker.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """Represents a storage node in the network."""

    node_id: str          # Unique identifier for the node
    address: str          # HTTP address (e.g. http://storage-node-1:9000)
    last_seen: float = 0  # Timestamp of last heartbeat
    chunks: Set[str] = field(default_factory=set)  # Chunk hashes stored

    def to_dict(self) -> dict:
        """Serialize node info to dictionary."""
        return {
            "node_id": self.node_id,
            "address": self.address,
            "last_seen": self.last_seen,
            "chunk_count": len(self.chunks),
        }


def _xor_distance(id_a: str, id_b: str) -> int:
    """
    Compute the XOR distance between two hex-encoded IDs.

    The XOR distance is the standard metric used in Kademlia DHTs.
    Closer nodes have smaller XOR distances.

    Args:
        id_a: Hex-encoded hash or node ID.
        id_b: Hex-encoded hash or node ID.

    Returns:
        Integer XOR distance.
    """
    # Hash both IDs to ensure consistent 256-bit representation
    hash_a = int(hashlib.sha256(id_a.encode()).hexdigest(), 16)
    hash_b = int(hashlib.sha256(id_b.encode()).hexdigest(), 16)
    return hash_a ^ hash_b


class RoutingTable:
    """
    Kademlia-style routing table for managing storage nodes
    and tracking chunk locations.

    Provides:
        - Node registration and heartbeat tracking
        - XOR-distance-based nearest-node lookup
        - Chunk location storage and retrieval
        - Stale node eviction
    """

    def __init__(self, stale_timeout: int = 60):
        """
        Initialize the routing table.

        Args:
            stale_timeout: Seconds before a node without heartbeat
                           is considered stale and evicted.
        """
        self._nodes: Dict[str, NodeInfo] = {}
        self._chunk_locations: Dict[str, Set[str]] = {}  # chunk_hash -> {node_ids}
        self._stale_timeout = stale_timeout
        logger.info(
            "Initialized routing table (stale_timeout=%ds)", stale_timeout
        )

    def register_node(self, node_id: str, address: str) -> NodeInfo:
        """
        Register a new storage node or update an existing one.

        Args:
            node_id: Unique node identifier.
            address: HTTP address of the node.

        Returns:
            The registered NodeInfo object.
        """
        now = time.time()
        if node_id in self._nodes:
            # Update existing node
            node = self._nodes[node_id]
            node.address = address
            node.last_seen = now
            logger.info("Updated node %s at %s", node_id, address)
        else:
            # Register new node
            node = NodeInfo(
                node_id=node_id, address=address, last_seen=now
            )
            self._nodes[node_id] = node
            logger.info("Registered new node %s at %s", node_id, address)
        return node

    def heartbeat(self, node_id: str) -> bool:
        """
        Update the last-seen timestamp for a node.

        Args:
            node_id: The node to heartbeat.

        Returns:
            True if the node exists and was updated, False otherwise.
        """
        if node_id in self._nodes:
            self._nodes[node_id].last_seen = time.time()
            logger.debug("Heartbeat from node %s", node_id)
            return True
        logger.warning("Heartbeat from unknown node %s", node_id)
        return False

    def remove_stale_nodes(self) -> List[str]:
        """
        Remove nodes that haven't sent a heartbeat within the timeout.

        Returns:
            List of removed node IDs.
        """
        now = time.time()
        stale_ids = [
            nid
            for nid, node in self._nodes.items()
            if now - node.last_seen > self._stale_timeout
        ]
        for nid in stale_ids:
            # Remove node from all chunk location records
            for chunk_hash in list(self._chunk_locations.keys()):
                self._chunk_locations[chunk_hash].discard(nid)
                if not self._chunk_locations[chunk_hash]:
                    del self._chunk_locations[chunk_hash]
            del self._nodes[nid]
            logger.info("Evicted stale node %s", nid)
        return stale_ids

    def get_active_nodes(self) -> List[NodeInfo]:
        """Return all currently registered (non-stale) nodes."""
        self.remove_stale_nodes()
        return list(self._nodes.values())

    def lookup_nodes(self, target_hash: str, k: int = 3) -> List[NodeInfo]:
        """
        Find the k closest active nodes to a target hash using XOR distance.

        Args:
            target_hash: The chunk hash or key to look up.
            k: Number of closest nodes to return.

        Returns:
            List of up to k NodeInfo objects, sorted by XOR distance.
        """
        self.remove_stale_nodes()
        if not self._nodes:
            return []

        # Sort all nodes by XOR distance to the target hash
        sorted_nodes = sorted(
            self._nodes.values(),
            key=lambda n: _xor_distance(n.node_id, target_hash),
        )
        return sorted_nodes[:k]

    def store_chunk_location(self, chunk_hash: str, node_id: str) -> None:
        """
        Record that a specific chunk is stored on a specific node.

        Args:
            chunk_hash: SHA-256 hash of the chunk.
            node_id: ID of the node storing the chunk.
        """
        if chunk_hash not in self._chunk_locations:
            self._chunk_locations[chunk_hash] = set()
        self._chunk_locations[chunk_hash].add(node_id)

        # Also update the node's chunk set
        if node_id in self._nodes:
            self._nodes[node_id].chunks.add(chunk_hash)

        logger.debug(
            "Recorded chunk %s on node %s", chunk_hash[:16], node_id
        )

    def get_chunk_locations(self, chunk_hash: str) -> List[NodeInfo]:
        """
        Find all nodes that store a given chunk.

        Args:
            chunk_hash: SHA-256 hash of the chunk to locate.

        Returns:
            List of NodeInfo objects for nodes storing the chunk.
        """
        self.remove_stale_nodes()
        node_ids = self._chunk_locations.get(chunk_hash, set())
        nodes = [
            self._nodes[nid]
            for nid in node_ids
            if nid in self._nodes
        ]
        logger.debug(
            "Chunk %s found on %d nodes", chunk_hash[:16], len(nodes)
        )
        return nodes

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """Get a specific node by ID, or None if not found."""
        return self._nodes.get(node_id)

    @property
    def node_count(self) -> int:
        """Return the number of registered nodes."""
        return len(self._nodes)

    @property
    def chunk_count(self) -> int:
        """Return the number of tracked chunks."""
        return len(self._chunk_locations)
