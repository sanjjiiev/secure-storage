import requests
import socket
import os
import file_handler # Your previous script (must be in same folder)

# CONFIGURATION
# REPLACE THIS IP with your Discovery Server's actual IP
DISCOVERY_SERVER_URL = "http://10.230.2.217:8000" 

def get_active_nodes():
    """Asks the Phonebook for a list of active IPs"""
    try:
        response = requests.get(f"{DISCOVERY_SERVER_URL}/get_nodes")
        nodes = response.json() # Returns ["192.168.1.5:5001", "10.0.0.2:5001"]
        print(f"[*] Found Active Nodes: {nodes}")
        return nodes
    except:
        print("[-] Discovery Server Offline or Unreachable.")
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

def record_to_blockchain(owner, file_hash, file_name, location_map):
    """Sends the metadata to the Blockchain on the Discovery Server"""
    payload = {
        "owner": owner,
        "file_hash": file_hash,
        "file_name": file_name,
        "locations": location_map
    }
    try:
        response = requests.post(f"{DISCOVERY_SERVER_URL}/add_transaction", json=payload)
        if response.status_code == 201:
            print("[+] Blockchain Updated: File locations recorded successfully.")
        else:
            print(f"[-] Blockchain Error: {response.text}")
    except Exception as e:
        print(f"[-] Failed to write to Blockchain: {e}")

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
        print("[!] No nodes available to store files! (Is a Storage Node running?)")
        return

    # 4. Distribute & Track Locations
    location_map = {} # Stores where each chunk went { "chunk_0": "192.168.1.5" }
    
    print("[*] Distributing chunks to network...")
    for i, chunk_name in enumerate(chunk_names):
        # Round Robin Selection: Chunk 0 -> Node A, Chunk 1 -> Node B...
        node_str = nodes[i % len(nodes)] 
        ip, port = node_str.split(":")
        
        success = upload_chunk(ip, port, chunk_name)
        if success:
            # Record the successful location
            base_chunk_name = os.path.basename(chunk_name)
            location_map[base_chunk_name] = ip 
        else:
            print(f"[!] Critical: Failed to upload chunk {i}")

    # 5. Generate Merkle Root (The File ID)
    merkle_root = handler.build_merkle_tree(chunks)
    
    # 6. Write to Blockchain
    if location_map:
        record_to_blockchain("User_A", merkle_root, file_to_upload, location_map)
    else:
        print("[-] Upload failed. No chunks were stored, so nothing to write to Blockchain.")

    print("\n--- UPLOAD COMPLETE ---")
    print(f"File ID (Merkle Root): {merkle_root}")
    print(f"Decryption Key: {key.decode()}")
    print("(Save this Key and Root safely! You need them to download.)")

if __name__ == "__main__":
    # Create a dummy file if needed
    if not os.path.exists("my_secret_data.txt"):
        with open("my_secret_data.txt", "w") as f: 
            f.write("Top Secret Project Data " * 500)
        
    main_upload_flow("my_secret_data.txt")