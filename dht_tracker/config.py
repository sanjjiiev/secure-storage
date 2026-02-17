"""
config.py — DHT Tracker Configuration
=======================================
Loads settings from environment variables with sensible defaults.
"""

import os


class Settings:
    """DHT Tracker configuration loaded from environment."""

    HOST: str = os.getenv("DHT_TRACKER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("DHT_TRACKER_PORT", "8500"))
    NODE_STALE_TIMEOUT: int = int(os.getenv("NODE_STALE_TIMEOUT", "60"))


settings = Settings()
