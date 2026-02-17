import socket
import threading
import os
import time
import requests
import json

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
# UPDATE THIS to your Hugging Face Spaces URL
HF_SPACE_URL = "https://Sanjjiiev-blockdrive.hf.space"

STORAGE_DIR = "node_storage"
PORT = 25565  # The local port matching Playit

# Your specific Playit Tunnel Address
HARDCODED_PUBLIC_HOST = "housing-obligations.gl.joinmc.link"
HARDCODED_PUBLIC_PORT = 25565

# Heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 60


# ─────────────────────────────────────────────
# REGISTRATION (talks to HF Spaces Gradio API)
# ─────────────────────────────────────────────
def register_with_discovery():
    """
    Register this node with the HF Spaces app.
    """
    try:
        payload = {
            "ip": HARDCODED_PUBLIC_HOST,
            "port": HARDCODED_PUBLIC_PORT
        }
        resp = requests.post(
            f"{HF_SPACE_URL}/api/register",
            json=payload,
            timeout=15
        )
        if resp.status_code == 200:
            print(f"[+] Registration OK: {HARDCODED_PUBLIC_HOST}:{HARDCODED_PUBLIC_PORT}")
            return True
        else:
            print(f"[-] Registration failed (HTTP {resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        print(f"[-] Registration error: {e}")
        return False


def heartbeat_loop():
    """
    Re-registers with the discovery server every HEARTBEAT_INTERVAL seconds.
    Keeps the node alive in the phonebook.
    """
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        print(f"[*] Heartbeat: re-registering...")
        register_with_discovery()


# ─────────────────────────────────────────────
# CLIENT HANDLER (TCP)
# ─────────────────────────────────────────────
def handle_client(conn, addr):
    """Handle an incoming TCP connection (upload or download)"""
    try:
        request = conn.recv(1024).decode()

        if request.startswith("GET:"):
            # ── Download request ──
            filename = request.split(":", 1)[1]
            path = os.path.join(STORAGE_DIR, filename)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    conn.sendall(f.read())
                print(f"[+] Sent: {filename} to {addr}")
            else:
                print(f"[-] File not found: {filename}")
        else:
            # ── Upload request ──
            # 'request' is the filename
            conn.send(b"ACK")
            path = os.path.join(STORAGE_DIR, request)
            with open(path, "wb") as f:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
            print(f"[+] Stored: {request} from {addr}")
    except Exception as e:
        print(f"[-] Error handling {addr}: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def start_node():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

    # Initial registration
    register_with_discovery()

    # Start heartbeat in background
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()
    print(f"[*] Heartbeat started (every {HEARTBEAT_INTERVAL}s)")

    # Start TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', PORT))
        server.listen(5)
        print(f"[*] Storage Node Active on port {PORT}")
        print(f"[*] Public address: {HARDCODED_PUBLIC_HOST}:{HARDCODED_PUBLIC_PORT}")
        print(f"[*] Waiting for connections...")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except OSError as e:
        print(f"[!] Port {PORT} already in use. Node may already be running.")
    except KeyboardInterrupt:
        print("\n[*] Node shutting down.")
        server.close()


if __name__ == "__main__":
    start_node()