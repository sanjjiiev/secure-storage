"""
main.py — Storage Node Service Entrypoint
============================================
Runs a storage node that stores encrypted file chunks,
registers with the DHT tracker, and sends periodic heartbeats.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from api.routes import router
from config import settings

# ── Logging Configuration ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(f"storage-node-{settings.NODE_ID}")


async def register_with_tracker():
    """Register this node with the DHT tracker."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.DHT_TRACKER_URL}/nodes/register",
                json={
                    "node_id": settings.NODE_ID,
                    "address": settings.NODE_ADVERTISE_URL,
                },
            )
            response.raise_for_status()
            logger.info(
                "Registered with DHT tracker at %s as %s (%s)",
                settings.DHT_TRACKER_URL,
                settings.NODE_ID,
                settings.NODE_ADVERTISE_URL,
            )
    except Exception as e:
        logger.error("Failed to register with DHT tracker: %s", e)


async def heartbeat_loop():
    """Send periodic heartbeats to the DHT tracker."""
    while True:
        try:
            await asyncio.sleep(settings.HEARTBEAT_INTERVAL)
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    f"{settings.DHT_TRACKER_URL}/nodes/heartbeat",
                    json={"node_id": settings.NODE_ID},
                )
                logger.debug("Heartbeat sent to DHT tracker")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: register with tracker and start heartbeat."""
    logger.info(
        "Storage Node %s starting on port %d (data_dir=%s)",
        settings.NODE_ID,
        settings.PORT,
        settings.DATA_DIR,
    )
    # Register with DHT tracker
    await register_with_tracker()

    # Start heartbeat background task
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    yield

    # Cleanup
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    logger.info("Storage Node %s shutting down", settings.NODE_ID)


# ── FastAPI Application ───────────────────────────────────
app = FastAPI(
    title=f"Storage Node {settings.NODE_ID}",
    description="Decentralized storage node for encrypted file chunks.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
