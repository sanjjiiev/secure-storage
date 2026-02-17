"""
main.py — Gateway Service Entrypoint
========================================
Runs the FastAPI gateway that provides the main REST API for
the decentralized file storage system.
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
logger = logging.getLogger("gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(
        "Gateway starting on %s:%d", settings.HOST, settings.PORT
    )
    logger.info("DHT Tracker: %s", settings.DHT_TRACKER_URL)
    logger.info("Blockchain:  %s", settings.BLOCKCHAIN_URL)
    logger.info("Chunk size:  %d bytes", settings.CHUNK_SIZE)
    logger.info("Replication: k=%d", settings.REPLICATION_FACTOR)
    yield
    logger.info("Gateway shutting down")


# ── FastAPI Application ───────────────────────────────────
app = FastAPI(
    title="Decentralized File Storage — Gateway API",
    description=(
        "REST API for uploading, downloading, and managing files "
        "in a blockchain-based decentralized storage system.\n\n"
        "**Upload:** File → split → encrypt → hash → Merkle tree "
        "→ replicate → blockchain\n\n"
        "**Download:** Blockchain → DHT → retrieve → verify → "
        "decrypt → reassemble"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router)
