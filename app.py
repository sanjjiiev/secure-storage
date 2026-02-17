import streamlit as st
import requests
import socket
import os
import file_handler
import json
from io import BytesIO

# --- CONFIGURATION ---
# UPDATE THIS IP to your Discovery Server's IP
DISCOVERY_SERVER = "http://10.230.2.217:8000"

# --- NETWORK FUNCTIONS ---
def get_active_nodes():
    try:
        response = requests.get(f"{DISCOVERY_SERVER}/get_nodes")
        if response.status_code == 200:
            return response.json()
    except:
        return []
    return []

def upload_chunk_to_node(ip, port, data, filename):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, int(port)))
        
        # Send Filename
        s.send(filename.encode())
        
        # Wait for ACK
        if s.recv(1024) != b"ACK": return False
        
        # Send Data
        s.sendall(data)
        s.close()
        return True
    except Exception as e:
        print(f"Error uploading to {ip}: {e}")
        return False

def download_chunk_from_node(ip, port, filename):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, int(port)))
        
        # Request File: "GET filename"
        # Note: We need to update smart_node.py slightly to handle "GET" requests
        # But for now, we assume the node just expects a filename to *download*? 
        # Actually, our current smart_node ONLY accepts uploads.
        # We need to fix smart_node logic below. 
        # For this prototype, we will assume standard socket behavior:
        # We send filename -> Node sends bytes back.
        
        # (This part requires the node to support download, see Step 3)
        s.send(f"GET:{filename}".encode()) 
        
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk: break
            data += chunk
        s.close()
        return data
    except:
        return None

def record_transaction(owner, file_hash, filename, locations):
    payload = {
        "owner": owner,
        "file_hash": file_hash,
        "file_name": filename,
        "locations": locations
    }
    try:
        requests.post(f"{DISCOVERY_SERVER}/add_transaction", json=payload)
        return True
    except:
        return False

# --- STREAMLIT UI ---
st.set_page_config(page_title="BlockDrive Secure Storage", layout="wide")
st.title("🔒 BlockDrive: Decentralized Secure Storage")

# Sidebar for Navigation
menu = st.sidebar.selectbox("Menu", ["Upload File", "Download File", "Blockchain Explorer"])

handler = file_handler.FileHandler()

if menu == "Upload File":
    st.header("Upload a File to the Network")
    
    # 1. User Inputs
    uploaded_file = st.file_uploader("Choose a file")
    username = st.text_input("Your Name (Owner ID)", "User_A")
    
    if uploaded_file and st.button("Encrypt & Upload"):
        # Progress Bar
        progress = st.progress(0)
        status_text = st.empty()
        
        # A. Encryption
        status_text.text("Encrypting file...")
        file_bytes = uploaded_file.getvalue()
        key = handler.generate_key()
        
        # We need to encrypt bytes directly, not from file path (Streamlit works in memory)
        f_fernet = file_handler.Fernet(key)
        encrypted_data = f_fernet.encrypt(file_bytes)
        progress.progress(20)
        
        # B. Sharding
        status_text.text("Splitting file into chunks...")
        # Split in memory
        chunk_size = 1024 * 1024 # 1MB
        chunks = [encrypted_data[i:i+chunk_size] for i in range(0, len(encrypted_data), chunk_size)]
        progress.progress(40)
        
        # C. Get Nodes
        nodes = get_active_nodes()
        if not nodes:
            st.error("No active storage nodes found! Start smart_node.py somewhere.")
        else:
            # D. Distribute
            status_text.text(f"Distributing {len(chunks)} chunks to {len(nodes)} nodes...")
            location_map = {}
            
            for i, chunk_data in enumerate(chunks):
                # Round Robin
                node_str = nodes[i % len(nodes)]
                ip, port = node_str.split(":")
                
                # Name: filename.enc_part_0
                chunk_name = f"{uploaded_file.name}.enc_part_{i}"
                
                if upload_chunk_to_node(ip, port, chunk_data, chunk_name):
                    location_map[chunk_name] = ip
                else:
                    st.warning(f"Failed to upload chunk {i} to {ip}")
            
            progress.progress(80)
            
            # E. Blockchain
            if location_map:
                # Calculate Merkle Root (using hash of chunk data)
                merkle_root = handler.build_merkle_tree(chunks)
                
                record_transaction(username, merkle_root, uploaded_file.name, location_map)
                progress.progress(100)
                status_text.text("Upload Complete!")
                
                st.success("File Successfully Stored on the Blockchain!")
                st.code(f"File ID (Merkle Root): {merkle_root}", language="text")
                st.code(f"Decryption Key: {key.decode()}", language="text")
                st.warning("SAVE THE KEY AND ID! You need them to download the file.")

elif menu == "Download File":
    st.header("Retrieve File from Network")
    
    file_id = st.text_input("File ID (Merkle Root)")
    decryption_key = st.text_input("Decryption Key")
    
    if st.button("Find & Download"):
        # 1. Ask Blockchain for Metadata
        try:
            resp = requests.get(f"{DISCOVERY_SERVER}/get_file/{file_id}")
            if resp.status_code != 200:
                st.error("File ID not found in Blockchain.")
            else:
                metadata = resp.json()
                locations = metadata['locations'] # {"part_0": "192.168.1.5", ...}
                st.info(f"File found! Metadata: {metadata['file_name']}")
                
                # 2. Download Chunks
                sorted_chunks = sorted(locations.keys(), key=lambda x: int(x.split('_')[-1]))
                full_encrypted_data = b""
                
                success = True
                for chunk_name in sorted_chunks:
                    node_ip = locations[chunk_name]
                    st.write(f"Fetching {chunk_name} from {node_ip}...")
                    
                    # We need a node download function (Mocked for now as we need to update node code)
                    # For this demo, we will assume if it runs locally it might work, 
                    # but typically you need to update smart_node.py to handle GET requests.
                    st.warning("Downloading logic requires updated smart_node.py (See instructions below)")
                    success = False 
                    break 
                
                if success:
                    # 3. Decrypt
                    try:
                        f_fernet = file_handler.Fernet(decryption_key.encode())
                        decrypted_data = f_fernet.decrypt(full_encrypted_data)
                        
                        st.download_button(
                            label="Download Decrypted File",
                            data=decrypted_data,
                            file_name=metadata['file_name']
                        )
                    except:
                        st.error("Decryption Failed! Wrong Key?")
                        
        except Exception as e:
            st.error(f"Error connecting to network: {e}")

elif menu == "Blockchain Explorer":
    st.header("Live Blockchain Ledger")
    
    if st.button("Refresh Chain"):
        try:
            # We need to add /chain to discovery server to make this work
            response = requests.get(f"{DISCOVERY_SERVER}/chain")
            if response.status_code == 200:
                chain_data = response.json()
                st.json(chain_data)
            else:
                st.error("Could not fetch chain.")
        except:
            st.error("Discovery Server is offline.")