"""
test_integration.py — Integration Tests
==========================================
End-to-end tests for the full upload/download pipeline.
These tests require the full system running via Docker Compose.

Run with:
    docker compose up -d
    docker compose run --rm gateway python -m pytest /app/tests/test_integration.py -v
"""

import base64
import hashlib
import os

import httpx
import pytest

# Gateway URL (inside Docker network)
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")
DHT_TRACKER_URL = os.getenv("DHT_TRACKER_URL", "http://dht-tracker:8500")


@pytest.fixture
def sample_file_content():
    """Generate sample file content for testing."""
    return b"Hello, Decentralized World! " * 1000  # ~28 KB


@pytest.fixture
def large_file_content():
    """Generate larger file content that spans multiple chunks."""
    return os.urandom(500_000)  # ~500 KB, will create 2 chunks


class TestSystemHealth:
    """Verify all services are running and healthy."""

    @pytest.mark.asyncio
    async def test_gateway_health(self):
        """Gateway should report healthy status."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GATEWAY_URL}/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["service"] == "gateway"
            assert data["blockchain_connected"] is True
            assert data["active_storage_nodes"] >= 1

    @pytest.mark.asyncio
    async def test_dht_tracker_health(self):
        """DHT tracker should report healthy status."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{DHT_TRACKER_URL}/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["service"] == "dht-tracker"
            assert data["active_nodes"] >= 1

    @pytest.mark.asyncio
    async def test_storage_nodes_registered(self):
        """All 3 storage nodes should be registered with DHT."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{DHT_TRACKER_URL}/nodes")
            assert resp.status_code == 200
            nodes = resp.json()
            assert len(nodes) >= 3


class TestUploadDownload:
    """End-to-end upload and download tests."""

    @pytest.mark.asyncio
    async def test_upload_file(self, sample_file_content):
        """Upload a file and verify response."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{GATEWAY_URL}/upload",
                files={"file": ("test.txt", sample_file_content)},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "file_id" in data
            assert "encryption_key" in data
            assert "merkle_root" in data
            assert data["chunk_count"] >= 1
            assert data["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_upload_and_download(self, sample_file_content):
        """Upload a file and download it — content should match."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Upload
            upload_resp = await client.post(
                f"{GATEWAY_URL}/upload",
                files={"file": ("roundtrip.txt", sample_file_content)},
            )
            assert upload_resp.status_code == 200
            upload_data = upload_resp.json()

            file_id = upload_data["file_id"]
            key = upload_data["encryption_key"]

            # Download
            download_resp = await client.get(
                f"{GATEWAY_URL}/download/{file_id}",
                params={"key": key},
            )
            assert download_resp.status_code == 200
            assert download_resp.content == sample_file_content

    @pytest.mark.asyncio
    async def test_upload_large_file(self, large_file_content):
        """Upload and download a file spanning multiple chunks."""
        async with httpx.AsyncClient(timeout=60) as client:
            # Upload
            upload_resp = await client.post(
                f"{GATEWAY_URL}/upload",
                files={"file": ("large.bin", large_file_content)},
            )
            assert upload_resp.status_code == 200
            data = upload_resp.json()
            assert data["chunk_count"] >= 2  # 500KB / 256KB = 2 chunks

            # Download
            download_resp = await client.get(
                f"{GATEWAY_URL}/download/{data['file_id']}",
                params={"key": data["encryption_key"]},
            )
            assert download_resp.status_code == 200
            assert download_resp.content == large_file_content


class TestFileManagement:
    """Test file listing and verification."""

    @pytest.mark.asyncio
    async def test_list_files(self, sample_file_content):
        """Uploaded files should appear in the file list."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Upload a file first
            await client.post(
                f"{GATEWAY_URL}/upload",
                files={"file": ("listed.txt", sample_file_content)},
            )

            # List files
            resp = await client.get(f"{GATEWAY_URL}/files")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_files"] >= 1

    @pytest.mark.asyncio
    async def test_verify_file(self, sample_file_content):
        """File verification (PoR) should succeed after upload."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Upload
            upload_resp = await client.post(
                f"{GATEWAY_URL}/upload",
                files={"file": ("verify.txt", sample_file_content)},
            )
            upload_data = upload_resp.json()
            file_id = upload_data["file_id"]

            # Verify
            verify_resp = await client.get(
                f"{GATEWAY_URL}/files/{file_id}/verify"
            )
            assert verify_resp.status_code == 200
            data = verify_resp.json()
            assert data["merkle_root_valid"] is True
