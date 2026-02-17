import socket
import threading
import os
import requests

# --- HARDCODED CONFIGURATION ---
DISCOVERY_SERVER_URL = "https://ss-server-5v34.onrender.com"
STORAGE_DIR = "node_storage"
PORT = 25565 # The local port matching Playit

# Your specific Playit Tunnel Address
HARDCODED_PUBLIC_HOST = "housing-obligations.gl.joinmc.link"
HARDCODED_PUBLIC_PORT = 25565

def register_with_discovery():
    """
    Automatically registers the node using the hardcoded Playit tunnel.
    """
    try:
        # We send the public tunnel address so others can reach this node
        payload = {
            "ip": HARDCODED_PUBLIC_HOST, 
            "port": HARDCODED_PUBLIC_PORT
        }
        requests.post(f"{DISCOVERY_SERVER_URL}/register", json=payload)
        print(f"[+] Automatic Registration Successful: {HARDCODED_PUBLIC_HOST}:{HARDCODED_PUBLIC_PORT}")
    except Exception as e:
        print(f"[-] Auto-Registration failed: {e}")

def handle_client(conn, addr):
    try:
        request = conn.recv(1024).decode()
        if request.startswith("GET:"):
            filename = request.split(":")[1]
            path = os.path.join(STORAGE_DIR, filename)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    conn.sendall(f.read())
        else:
            conn.send(b"ACK")
            path = os.path.join(STORAGE_DIR, request)
            with open(path, "wb") as f:
                while True:
                    data = conn.recv(4096)
                    if not data: break
                    f.write(data)
    finally:
        conn.close()

def start_node():
    if not os.path.exists(STORAGE_DIR): 
        os.makedirs(STORAGE_DIR)
    
    # Trigger the automatic registration
    register_with_discovery()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', PORT))
        server.listen(5)
        print(f"[*] Background Node Active on Port {PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    except Exception as e:
        # This prevents crashing if the user refreshes Streamlit
        print(f"[*] Node already running or port bound.")