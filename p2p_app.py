import streamlit as st
import threading
import smart_node
import requests
import socket
import file_handler

# --- CONFIGURATION ---
DISCOVERY_SERVER = "https://ss-server-5v34.onrender.com"

# --- 1. AUTO-START LOGIC ---
if "node_running" not in st.session_state:
    st.session_state["node_running"] = True
    # Start the hardcoded node automatically
    node_thread = threading.Thread(target=smart_node.start_node, daemon=True)
    node_thread.start()

# --- 2. CLIENT HELPER FUNCTIONS ---
def get_peers():
    try:
        response = requests.get(f"{DISCOVERY_SERVER}/get_nodes")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def upload_chunk(ip, port, data, filename):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, int(port)))
        s.send(filename.encode())
        if s.recv(1024) != b"ACK": return False
        s.sendall(data)
        s.close()
        return True
    except:
        return False

def download_chunk(ip, port, filename):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, int(port)))
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

# --- 3. STREAMLIT UI ---
st.set_page_config(page_title="BlockDrive P2P", layout="wide")
st.title("🌐 BlockDrive: Automated P2P Storage")
st.caption("✅ Background Node Active. You are currently a storage provider.")

# Sidebar status
peers = get_peers()
st.sidebar.metric("Active Peers", len(peers))
if st.sidebar.button("Refresh Network"):
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📤 Upload", "📥 Download", "🔗 Blockchain"])

with tab1:
    st.header("Upload File to Network")
    uploaded_file = st.file_uploader("Choose a file")
    
    if uploaded_file and st.button("Distribute Encrypted Chunks"):
        handler = file_handler.FileHandler()
        file_bytes = uploaded_file.getvalue()
        
        # Encrypt
        key = handler.generate_key()
        f = file_handler.Fernet(key)
        encrypted_data = f.encrypt(file_bytes)
        
        # Split (1MB chunks)
        chunk_size = 1024 * 1024
        chunks = [encrypted_data[i:i+chunk_size] for i in range(0, len(encrypted_data), chunk_size)]
        
        if not peers:
            st.error("No other nodes detected on the network.")
        else:
            location_map = {}
            progress = st.progress(0)
            for i, chunk_data in enumerate(chunks):
                peer = peers[i % len(peers)]
                p_ip, p_port = peer.split(":")
                c_name = f"{uploaded_file.name}.part_{i}"
                
                if upload_chunk(p_ip, p_port, chunk_data, c_name):
                    location_map[c_name] = p_ip
                progress.progress((i+1)/len(chunks))
            
            # Record to Blockchain (Render)
            root = handler.build_merkle_tree(chunks)
            payload = {
                "owner": "User_Me", 
                "file_hash": root, 
                "file_name": uploaded_file.name, 
                "locations": location_map
            }
            requests.post(f"{DISCOVERY_SERVER}/add_transaction", json=payload)
            
            st.success(f"File ID: {root}")
            st.warning(f"Decryption Key: {key.decode()}")

with tab2:
    st.header("Retrieve & Reassemble")
    f_id = st.text_input("File ID")
    f_key = st.text_input("Key")
    
    if st.button("Download"):
        resp = requests.get(f"{DISCOVERY_SERVER}/get_file/{f_id}")
        if resp.status_code == 200:
            meta = resp.json()
            locs = meta['locations']
            full_data = b""
            for c_name in sorted(locs.keys()):
                data = download_chunk(locs[c_name], 25565, c_name)
                if data: full_data += data
            
            try:
                f = file_handler.Fernet(f_key.encode())
                decrypted = f.decrypt(full_data)
                st.download_button("Download Original", decrypted, file_name=meta['file_name'])
            except:
                st.error("Invalid Key")

with tab3:
    if st.button("View Ledger"):
        chain_data = requests.get(f"{DISCOVERY_SERVER}/chain").json()
        st.json(chain_data)