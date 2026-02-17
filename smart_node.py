import requests
import time
import os
import uuid
import json
import sys

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
# REPLACE THIS WITH YOUR HF SPACE URL (e.g. https://huggingface.co/spaces/...)
# Ensure no trailing slash
HF_SPACE_URL = "https://sanjjiiev-blockdrive.hf.space"

NODE_ID_FILE = "node_id.txt"
STORAGE_DIR = "node_storage"

# Load or generate persistent Node ID
if os.path.exists(NODE_ID_FILE):
    with open(NODE_ID_FILE, "r") as f:
        NODE_ID = f.read().strip()
else:
    NODE_ID = f"relay-node-{uuid.uuid4().hex[:8]}"
    with open(NODE_ID_FILE, "w") as f:
        f.write(NODE_ID)

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

print(f"🚀 Starting BlockDrive Storage Node (Relay Mode)")
print(f"🆔 Node ID: {NODE_ID}")
print(f"📂 Storage: {os.path.abspath(STORAGE_DIR)}")
print(f"🔗 Connecting to: {HF_SPACE_URL}")

def register():
    try:
        # We register with port 0 to indicate "Relay Mode" (or just standard)
        payload = {"ip": NODE_ID, "port": 0}
        resp = requests.post(f"{HF_SPACE_URL}/api/register", json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"[+] Heartbeat sent. Online.")
        else:
            print(f"[-] Register failed: {resp.text}")
    except Exception as e:
        print(f"[-] Connection failed: {e}")

def process_tasks():
    try:
        resp = requests.get(f"{HF_SPACE_URL}/api/poll_tasks", params={"node_id": NODE_ID}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            tasks = data.get("tasks", [])
            
            for task in tasks:
                if task.get("type") == "store":
                    chunk_name = task.get("chunk_name")
                    print(f"📥 Downloading chunk: {chunk_name}...")
                    
                    # Download from Relay
                    r_file = requests.get(f"{HF_SPACE_URL}/api/download_relay/{chunk_name}", timeout=30)
                    if r_file.status_code == 200:
                        path = os.path.join(STORAGE_DIR, chunk_name)
                        with open(path, "wb") as f:
                            f.write(r_file.content)
                        
                        print(f"✅ Stored {chunk_name} ({len(r_file.content)} bytes)")
                        
                        # Confirm
                        requests.post(f"{HF_SPACE_URL}/api/confirm_task", params={
                            "node_id": NODE_ID,
                            "chunk_name": chunk_name,
                            "status": "success"
                        })
                    else:
                        print(f"❌ Failed to download {chunk_name}: {r_file.status_code}")
                
                elif task.get("type") == "retrieve":
                    chunk_name = task.get("chunk_name")
                    print(f"📤 Serving request for chunk: {chunk_name}...")
                    
                    path = os.path.join(STORAGE_DIR, chunk_name)
                    if os.path.exists(path):
                        try:
                            with open(path, "rb") as f:
                                files = {"file": (chunk_name, f)}
                                data = {"chunk_name": chunk_name}
                                # Push to Relay
                                r = requests.post(f"{HF_SPACE_URL}/api/relay_push", 
                                                files=files, data=data, timeout=60)
                                if r.status_code == 200:
                                    print(f"✅ Pushed {chunk_name} to relay")
                                else:
                                    print(f"❌ Failed to push {chunk_name}: {r.text}")
                        except Exception as e:
                            print(f"❌ Error pushing {chunk_name}: {e}")
                    else:
                        print(f"❌ Requested chunk not found: {chunk_name}")
    except Exception as e:
        print(f"[-] Error polling: {e}")

# ─────────────────────────────────────────────
# BLOCKCHAIN SYNC (Decentralization)
# ─────────────────────────────────────────────
LOCAL_CHAIN_FILE = "local_chain.json"

def sync_blockchain():
    """Fetch and validate the blockchain from the backend.
    Each node keeps a local verified copy for decentralization."""
    try:
        r = requests.get(f"{HF_SPACE_URL}/api/chain", timeout=10)
        if r.status_code == 200:
            data = r.json()
            chain = data.get("chain", [])
            
            # Validate chain integrity locally
            v = requests.get(f"{HF_SPACE_URL}/api/validate", timeout=10)
            if v.status_code == 200:
                result = v.json()
                if result.get("valid"):
                    # Save verified chain locally
                    with open(LOCAL_CHAIN_FILE, "w") as f:
                        json.dump({"chain": chain, "synced_at": time.time()}, f, indent=2)
                    print(f"🔗 Chain synced & verified ({len(chain)} blocks)")
                else:
                    print(f"⚠️ WARNING: Backend chain TAMPERED at block {result.get('tampered_at')}!")
    except Exception as e:
        print(f"[-] Chain sync failed: {e}")

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
SYNC_INTERVAL = 12  # Sync chain every 12 polls (~60s)

def main():
    poll_count = 0
    while True:
        register()
        process_tasks()
        
        # Sync blockchain periodically
        poll_count += 1
        if poll_count % SYNC_INTERVAL == 0:
            sync_blockchain()
        
        time.sleep(5) # Poll every 5 seconds

if __name__ == "__main__":
    main()