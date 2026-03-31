# Secure Storage: Smart Node 

The client-side implementation of the P2P Decentralized File Storage System. This repository contains the `smart_node` architecture, allowing individual peers to securely encrypt, shard, and store data across a distributed network.

## Overview

`secure-storage` is designed with a focus on secure architecture and resilience. By utilizing localized chain tracking (`local_chain.bin`), each node independently verifies data integrity without relying on a centralized database for file retrieval. 

## 🛠️ Tech Stack
* **Language:** Python
* **Core Mechanisms:** Peer-to-peer (P2P) networking, cryptographic hashing, and local state management.
* **Environment:** Compatible across Windows, Linux (e.g., Ubuntu/Parrot), and macOS.

## Repository Structure
```text
secure-storage/
├── smart_node.py         # Core logic for the P2P node operations
├── local_chain.bin       # Binary ledger for local state and integrity tracking
├── node_id.txt           # Unique cryptographic identifier for the node
├── requirements.txt      # Python dependencies
└── .gitignore            # Git ignore rules
