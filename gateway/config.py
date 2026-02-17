"""
config.py — Gateway Configuration
====================================
"""

import os


class Settings:
    """Gateway configuration from environment."""

    HOST: str = os.getenv("GATEWAY_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("GATEWAY_PORT", "8000"))
    DHT_TRACKER_URL: str = os.getenv("DHT_TRACKER_URL", "http://localhost:8500")
    BLOCKCHAIN_URL: str = os.getenv("BLOCKCHAIN_URL", "http://localhost:8545")
    CONTRACT_ADDRESSES_FILE: str = os.getenv(
        "CONTRACT_ADDRESSES_FILE", "./contract_addresses.json"
    )
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "262144"))  # 256 KB
    REPLICATION_FACTOR: int = int(os.getenv("REPLICATION_FACTOR", "3"))


settings = Settings()
