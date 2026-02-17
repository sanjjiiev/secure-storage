import socket
import threading
import os
import requests
import miniupnpc

# CONFIGURATION
DISCOVERY_SERVER_URL = "http://10.230.2.217:8000" # <--- REPLACE with Discovery Server IP!
PORT = 5001
STORAGE_DIR = "node_storage"

def setup_upnp(port_no):
    """Attempts to forward ports using UPnP"""
    print(f"[*] Attempting UPnP Port Forwarding for port {port_no}...")
    try:
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 200
        upnp.discover()
        upnp.selectigd()
        
        # Get External IP
        external_ip = upnp.externalipaddress()
        
        # Add Port Mapping (External -> Internal)
        upnp.addportmapping(port_no, 'TCP', upnp.lanaddr, port_no, 'BlockDrive Node', '')
        print(f"[SUCCESS] UPnP Active! External IP: {external_ip}")
        return external_ip
    except Exception as e:
        print(f"[-] UPnP Failed: {e}. Assuming Local Network.")
        return None

def register_with_discovery(public_ip, port):
    """Tells the Discovery Server we are alive"""
    if not public_ip:
        # Fallback to local IP if UPnP failed
        public_ip = socket.gethostbyname(socket.gethostname())
        
    try:
        payload = {"ip": public_ip, "port": port}
        requests.post(f"{DISCOVERY_SERVER_URL}/register", json=payload)
        print("[+] Registered with Discovery Server.")
    except Exception as e:
        print(f"[-] Could not contact Discovery Server: {e}")

def handle_client(conn, addr):
    """Receives a file chunk"""
    print(f"[+] Connection from {addr}")
    try:
        # 1. Read Filename
        file_name = conn.recv(1024).decode()
        conn.send(b"ACK") # Send Acknowledgement

        # 2. Save File
        path = os.path.join(STORAGE_DIR, file_name)
        with open(path, "wb") as f:
            while True:
                data = conn.recv(4096)
                if not data: break
                f.write(data)
        print(f"[+] Stored chunk: {file_name}")
    except Exception as e:
        print(f"[-] Error receiving: {e}")
    finally:
        conn.close()

def start_node():
    if not os.path.exists(STORAGE_DIR): os.makedirs(STORAGE_DIR)
    
    # 1. Setup Networking
    public_ip = setup_upnp(PORT)
    
    # 2. Register Presence
    register_with_discovery(public_ip, PORT)
    
    # 3. Start Server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', PORT))
    server.listen(5)
    print(f"[*] Node listening on Port {PORT}...")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_node()