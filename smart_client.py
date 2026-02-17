import requests
import socket
import os
import file_handler # Your previous script!

# CONFIGURATION
DISCOVERY_SERVER_URL = "http://10.230.2.217:8000" # <--- REPLACE with Discovery Server IP!

def get_active_nodes():
    """Asks the Phonebook for a list of active IPs"""
    try:
        response = requests.get(f"{DISCOVERY_SERVER_URL}/get_nodes")
        nodes = response.json() # Returns ["192.168.1.5:5001", "10.0.0.2:5001"]
        print(f"[*] Found Active Nodes: {nodes}")
        return nodes
    except:
        print("[-] Discovery Server Offline.")
        return []

def upload_chunk(target_ip, target_port, file_path):
    """Sends a single chunk to a specific node"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((target_ip, int(target_port)))
        
        # Send Filename
        filename = os.path.basename(file_path)
        s.send(filename.encode())
        
        # Wait for ACK
        if s.recv(1024) != b"ACK": return False
        
        # Send Data
        with open(file_path, "rb") as f:
            s.sendall(f.read())
            
        s.close()
        print(f"[+] Uploaded {filename} to {target_ip}")
        return True
    except Exception as e:
        print(f"[-] Failed to upload to {target_ip}: {e}")
        return False

def main_upload_flow(file_to_upload):
    handler = file_handler.FileHandler()
    
    # 1. Encrypt
    key = handler.generate_key()
    print("[*] Encrypting file...")
    enc_file = handler.encrypt_file(file_to_upload, key)
    
    # 2. Split
    print("[*] Splitting file...")
    chunks, chunk_names = handler.split_file(enc_file)
    
    # 3. Get Nodes
    nodes = get_active_nodes()
    if not nodes:
        print("[!] No nodes available to store files!")
        return

    # 4. Distribute (Round Robin)
    print("[*] Distributing chunks to network...")
    for i, chunk_name in enumerate(chunk_names):
        # Pick a node: Chunk 0 -> Node A, Chunk 1 -> Node B, Chunk 2 -> Node A...
        node_str = nodes[i % len(nodes)] 
        ip, port = node_str.split(":")
        
        success = upload_chunk(ip, port, chunk_name)
        if not success:
            print(f"[!] Critical: Failed to upload chunk {i}")

    # 5. Generate Merkle Root (The "Blockchain Receipt")
    merkle_root = handler.build_merkle_tree(chunks)
    print("\n--- UPLOAD COMPLETE ---")
    print(f"File ID (Merkle Root): {merkle_root}")
    print(f"Decryption Key: {key.decode()}")
    print("(Save this Key and Root safely!)")

if __name__ == "__main__":
    # Create a dummy file if needed
    if not os.path.exists("my_secret_data.txt"):
        with open("my_secret_data.txt", "w") as f: f.write("Top Secret Project Data " * 500)
        
    main_upload_flow("my_secret_data.txt")