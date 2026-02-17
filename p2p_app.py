import streamlit as st
import threading
import smart_node  # Import your node script
import requests
import socket
import os
import file_handler
import time

# --- CONFIGURATION ---
# The Tracker (Phonebook) still runs on one stable PC (or cloud)
DISCOVERY_SERVER = "http://192.168.1.10:8000"  # <--- UPDATE THIS IP

# --- 1. AUTO-START STORAGE NODE (BACKGROUND) ---
# We use Streamlit's session state to ensure the node only starts ONCE
if "node_running" not in st.session_state:
    st.session_state["node_running"] = True
    
    # Run smart_node.start_node() in a separate thread
    # This ensures the GUI doesn't freeze while the node listens for files
    node_thread = threading.Thread(target=smart_node.start_node, daemon=True)
    node_thread.start()
    print("[*] Background Storage Node Started!")

# --- 2. CLIENT FUNCTIONS (For the UI) ---
def get_peers():
    try:
        response = requests.get(f"{DISCOVERY_SERVER}/get_nodes")
        if response.status_code == 200:
            nodes = response.json()
            # Filter out myself! (Don't upload to localhost if possible)
            # For this demo, we keep everyone.
            return nodes
    except:
        return []

def upload_chunk(ip, port, data, filename):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2) # Short timeout
        s.connect((ip, int(port)))
        s.send(filename.encode())
        if s.recv(1024) != b"ACK": return False
        s.sendall(data)
        s.close()
        return True
    except:
        return False

def record_transaction(owner, file_hash, filename, locations):
    payload = {"owner": owner, "file_hash": file_hash, "file_name": filename, "locations": locations}
    try:
        requests.post(f"{DISCOVERY_SERVER}/add_transaction", json=payload)
        return True
    except:
        return False

# --- 3. THE USER INTERFACE (Frontend) ---
st.set_page_config(page_title="BlockDrive P2P", layout="wide")

st.title("🌐 BlockDrive: P2P Secure Storage")
st.caption(f"✅ You are a Node! Contributing storage to the network.")

# Sidebar Stats
st.sidebar.header("Network Status")
peers = get_peers()
st.sidebar.metric("Active Peers", len(peers))
st.sidebar.text("Tracker: Online" if peers else "Tracker: Offline")

# Tabs for cleanliness
tab1, tab2, tab3 = st.tabs(["📤 Upload", "📥 Download", "🔗 Blockchain"])

with tab1:
    st.header("Upload to the Mesh")
    uploaded_file = st.file_uploader("Select a file")
    
    if uploaded_file and st.button("Distribute File"):
        handler = file_handler.FileHandler()
        
        # A. Encrypt
        with st.spinner("Encrypting..."):
            file_bytes = uploaded_file.getvalue()
            key = handler.generate_key()
            f_fernet = file_handler.Fernet(key)
            encrypted_data = f_fernet.encrypt(file_bytes)
        
        # B. Split
        chunk_size = 1024 * 1024 # 1MB
        chunks = [encrypted_data[i:i+chunk_size] for i in range(0, len(encrypted_data), chunk_size)]
        
        # C. Distribute
        if not peers:
            st.error("No peers found! You are the only one online.")
        else:
            progress_bar = st.progress(0)
            location_map = {}
            
            for i, chunk_data in enumerate(chunks):
                # Pick a random peer or round-robin
                peer = peers[i % len(peers)]
                ip, port = peer.split(":")
                
                chunk_name = f"{uploaded_file.name}.part_{i}"
                if upload_chunk(ip, port, chunk_data, chunk_name):
                    location_map[chunk_name] = ip
                progress_bar.progress((i + 1) / len(chunks))
            
            # D. Record
            if location_map:
                merkle_root = handler.build_merkle_tree(chunks)
                record_transaction("User_Me", merkle_root, uploaded_file.name, location_map)
                st.success("File Distributed Successfully!")
                st.info(f"File ID: {merkle_root}")
                st.warning(f"Key: {key.decode()}")

with tab2:
    st.header("Retrieve File")
    file_id = st.text_input("Enter File ID")
    dec_key = st.text_input("Enter Key")
    if st.button("Download"):
        st.info("Fetching metadata from Blockchain...")
        # (Add download logic here matching previous steps)
        # 1. Get Locations from Tracker
        # 2. Connect to Peer IPs
        # 3. Decrypt
        st.write("Searching network...")

with tab3:
    if st.button("Refresh Chain"):
        try:
            chain = requests.get(f"{DISCOVERY_SERVER}/chain").json()
            st.json(chain)
        except:
            st.error("Tracker unavailable")