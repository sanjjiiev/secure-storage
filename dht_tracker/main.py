"""
main.py — DHT Tracker Service Entrypoint
==========================================
Runs the Kademlia-style DHT tracker that manages storage node
registration, heartbeats, and chunk location tracking.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from config import settings

# ── Logging Configuration ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dht-tracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info(
        "DHT Tracker starting on %s:%d (stale_timeout=%ds)",
        settings.HOST,
        settings.PORT,
        settings.NODE_STALE_TIMEOUT,
    )
    yield
    logger.info("DHT Tracker shutting down")


# ── FastAPI Application ───────────────────────────────────
app = FastAPI(
    title="DHT Tracker — Decentralized File Storage",
    description=(
        "Kademlia-style DHT tracker for storage node discovery "
        "and chunk location tracking."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
