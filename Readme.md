# Blockchain-Based Decentralized File Storage System

A production-ready, modular system for **decentralized file storage** using cryptographic primitives, distributed hash tables, and blockchain-based metadata management.

**Upload:** File → Split → AES-256 Encrypt → SHA-256 Hash → Merkle Tree → Distribute to Nodes → Register on Blockchain  
**Download:** Blockchain Metadata → DHT Lookup → Retrieve Chunks → Verify Hashes → Decrypt → Reassemble

---

##  Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Client     │────▶│   Gateway    │────▶│  DHT Tracker     │
│  (REST API)  │     │  (FastAPI)   │     │  (Kademlia-style) │
└──────────────┘     └──────┬───────┘     └────────┬─────────┘
                            │                      │
                    ┌───────┴────────┐    ┌────────┴─────────┐
                    │   Blockchain   │    │  Storage Nodes    │
                    │   (Hardhat)    │    │  (3 instances)    │
                    │                │    │                   │
                    │ FileRegistry   │    │ ┌──────┐ ┌──────┐│
                    │ StorageProof   │    │ │Node 1│ │Node 2││
                    └────────────────┘    │ └──────┘ └──────┘│
                                          │ ┌──────┐         │
                                          │ │Node 3│         │
                                          │ └──────┘         │
                                          └──────────────────┘
```

### Components

| Component | Tech | Port | Description |
|-----------|------|------|-------------|
| **Gateway** | FastAPI (Python) | 8000 | REST API for upload/download orchestration |
| **DHT Tracker** | FastAPI (Python) | 8500 | Kademlia-style peer discovery & chunk routing |
| **Storage Nodes** (×3) | FastAPI (Python) | 9001-9003 | Encrypted chunk storage with PoR |
| **Blockchain** | Hardhat (Ethereum) | 8545 | File metadata & Merkle root registry |

---

##  Project Structure

```
secure-storage/
├── docker-compose.yml          # Full system orchestration
├── .env.example                # Environment variable template
│
├── blockchain/                 # Ethereum smart contracts
│   ├── contracts/
│   │   ├── FileRegistry.sol    # File metadata & Merkle root registry
│   │   └── StorageProof.sol    # Proof of Retrievability records
│   ├── scripts/deploy.js       # Auto-deployment script
│   ├── test/                   # Contract tests (Chai/Mocha)
│   ├── hardhat.config.js
│   └── Dockerfile
│
├── gateway/                    # API Gateway service
│   ├── main.py                 # FastAPI entrypoint
│   ├── api/
│   │   ├── routes.py           # Upload/download/verify endpoints
│   │   └── schemas.py          # Pydantic models
│   ├── core/
│   │   ├── chunker.py          # File splitting & reassembly
│   │   ├── encryption.py       # AES-256-CBC encrypt/decrypt
│   │   ├── hashing.py          # SHA-256 hashing
│   │   └── merkle.py           # Merkle tree with proof generation
│   ├── services/
│   │   ├── blockchain_client.py # Web3 contract interaction
│   │   ├── dht_client.py       # DHT tracker HTTP client
│   │   └── replication.py      # k-replica replication manager
│   └── Dockerfile
│
├── storage_node/               # Storage Node service
│   ├── main.py                 # Auto-registers with DHT, heartbeat
│   ├── api/routes.py           # Chunk CRUD + PoR challenge
│   ├── services/
│   │   ├── chunk_store.py      # Content-addressable filesystem store
│   │   └── proof.py            # Proof of Retrievability
│   └── Dockerfile
│
├── dht_tracker/                # DHT Tracker service
│   ├── main.py                 # Bootstrap node
│   ├── api/routes.py           # Node registration & chunk lookup
│   ├── services/
│   │   └── routing_table.py    # XOR distance routing table
│   └── Dockerfile
│
└── tests/                      # Test suite
    ├── test_chunker.py         # Unit: file chunking
    ├── test_encryption.py      # Unit: AES-256 encryption
    ├── test_merkle.py          # Unit: Merkle tree
    └── test_integration.py     # E2E: full pipeline
```

---

##  Quick Start (Docker)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose v2+
- Git

### 1. Clone & Configure

```bash
git clone <repo-url> secure-storage
cd secure-storage
cp .env.example .env
```

### 2. Build & Start All Services

```bash
docker compose up --build
```

This starts:
- **Hardhat node** (port 8545) — deploys smart contracts automatically
- **DHT Tracker** (port 8500) — bootstrap node for peer discovery
- **3 Storage Nodes** (ports 9001-9003) — register with DHT automatically
- **Gateway API** (port 8000) — waits for all services to be healthy

### 3. Verify Everything is Running

```bash
# Check system health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "gateway",
#   "blockchain_connected": true,
#   "active_storage_nodes": 3,
#   "total_files": 0
# }
```

### 4. Stop & Cleanup

```bash
docker compose down -v    # -v removes volumes (stored chunks)
```

---

## 📡 API Reference

### Upload a File

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "file_id": "a1b2c3d4...",
  "filename": "document.pdf",
  "encryption_key": "e4f5a6b7...",
  "merkle_root": "d8e9f0a1...",
  "chunk_count": 4,
  "chunk_hashes": ["abc...", "def...", "ghi...", "jkl..."],
  "replication_factor": 3,
  "blockchain_tx": "0x123...",
  "message": "File uploaded and distributed successfully"
}
```

>  **Save the `encryption_key`!** It is NOT stored anywhere on the server. You need it to download the file.

### Download a File

```bash
curl -X GET "http://localhost:8000/download/{file_id}?key={encryption_key}" \
  -o downloaded_file.pdf
```

### List All Files

```bash
curl http://localhost:8000/files
```

### Verify File Integrity (Proof of Retrievability)

```bash
curl http://localhost:8000/files/{file_id}/verify
```

**Response:**
```json
{
  "file_id": "a1b2c3d4...",
  "merkle_root_valid": true,
  "chunk_proofs": [
    {
      "chunk_hash": "abc...",
      "node_id": "node-1",
      "challenge": "random_nonce",
      "proof": "sha256_response",
      "is_valid": true
    }
  ],
  "all_valid": true,
  "message": "All chunks verified successfully"
}
```

### Interactive API Docs

Open http://localhost:8000/docs for **Swagger UI** or http://localhost:8000/redoc for **ReDoc**.

---

##  Testing

### Smart Contract Tests

```bash
cd blockchain
npm install
npx hardhat test
```

### Unit Tests (Python — requires gateway dependencies)

```bash
pip install -r gateway/requirements.txt
python -m pytest tests/test_chunker.py tests/test_encryption.py tests/test_merkle.py -v
```

### Integration Tests (requires Docker Compose running)

```bash
docker compose up -d
docker compose exec gateway python -m pytest /app/tests/test_integration.py -v
```

---

##  Security Architecture

| Layer | Mechanism | Details |
|-------|-----------|---------|
| **Encryption** | AES-256-CBC | Client-side; random IV per chunk; key never stored on server |
| **Integrity** | SHA-256 + Merkle Tree | Each chunk hashed; Merkle root stored on-chain |
| **Verification** | Proof of Retrievability | Challenge-response: `SHA-256(chunk ∥ nonce)` |
| **Blockchain** | Ethereum (Hardhat) | Immutable metadata registry; tamper-evident |
| **Replication** | k=3 replica strategy | Each chunk stored on 3 nodes for fault tolerance |

---

## 🌐 Multi-PC Deployment

To run across multiple physical machines:

### PC 1 — Infrastructure (Blockchain + DHT)

```bash
# Run blockchain and DHT tracker
docker compose up hardhat dht-tracker
```

### PC 2, 3, 4 — Storage Nodes

On each PC, run a storage node pointing to the DHT tracker:

```bash
docker run -d \
  -e STORAGE_NODE_PORT=9000 \
  -e DHT_TRACKER_URL=http://<PC1_IP>:8500 \
  -e NODE_ID=node-pc2 \
  -e NODE_ADVERTISE_URL=http://<THIS_PC_IP>:9000 \
  -v storage_data:/data/chunks \
  -p 9000:9000 \
  secure-storage-storage-node
```

### Any PC — Gateway

```bash
docker run -d \
  -e DHT_TRACKER_URL=http://<PC1_IP>:8500 \
  -e BLOCKCHAIN_URL=http://<PC1_IP>:8545 \
  -e CONTRACT_ADDRESSES_FILE=/shared/contract_addresses.json \
  -v shared_data:/shared \
  -p 8000:8000 \
  secure-storage-gateway
```

---

##  Fault Tolerance

The system is designed to handle node failures:

1. **Replication (k=3):** Every chunk is stored on 3 different nodes
2. **Heartbeat monitoring:** Nodes send heartbeats every 15 seconds
3. **Stale eviction:** Nodes without heartbeat for 60s are removed from DHT
4. **Download resilience:** If one node is down, chunks are fetched from replicas
5. **Replication repair:** `ReplicationManager.repair_replication()` re-replicates under-replicated chunks

### Test Fault Tolerance

```bash
# Start system
docker compose up -d

# Upload a file
curl -X POST http://localhost:8000/upload -F "file=@test.txt"
# Save the file_id and encryption_key

# Kill one storage node
docker compose stop storage-node-2

# Download should still succeed
curl "http://localhost:8000/download/{file_id}?key={key}" -o result.txt

# Verify content matches
diff test.txt result.txt
```

---

##  Tech Stack

| Category | Technology |
|----------|-----------|
| Backend API | Python 3.11 + FastAPI |
| Smart Contracts | Solidity 0.8.24 |
| Blockchain Dev | Hardhat + Ethers.js |
| Encryption | PyCryptodome (AES-256-CBC) |
| Blockchain Client | Web3.py |
| HTTP Client | httpx (async) |
| Containerization | Docker + Docker Compose |
| Testing | pytest (Python) + Chai/Mocha (JS) |

---

##  License

MIT
