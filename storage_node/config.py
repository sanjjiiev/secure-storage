"""
config.py — Storage Node Configuration
========================================
"""

import os


class Settings:
    """Storage Node configuration from environment."""

    PORT: int = int(os.getenv("STORAGE_NODE_PORT", "9000"))
    DATA_DIR: str = os.getenv("STORAGE_DATA_DIR", "/data/chunks")
    DHT_TRACKER_URL: str = os.getenv("DHT_TRACKER_URL", "http://localhost:8500")
    NODE_ID: str = os.getenv("NODE_ID", "node-default")
    NODE_ADVERTISE_URL: str = os.getenv("NODE_ADVERTISE_URL", "http://localhost:9000")
    HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "15"))


settings = Settings()
