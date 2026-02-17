import socket
import os

# CONFIGURATION
HOST = '0.0.0.0'  # Listen on all network interfaces (WiFi, Ethernet)
PORT = 5001       # The port this node listens on
STORAGE_DIR = "node_storage"

# Create storage directory if not exists
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def start_server():
    # 1. Create a Socket (TCP/IP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 2. Bind to the Port
    server_socket.bind((HOST, PORT))
    
    # 3. Start Listening (Queue up to 5 connections)
    server_socket.listen(5)
    print(f"[*] Node Started. Listening on {HOST}:{PORT}...")
    print(f"[*] storage_dir: {STORAGE_DIR}")

    while True:
        # 4. Accept Incoming Connection
        client_socket, addr = server_socket.accept()
        print(f"[+] Connection from {addr}")
        
        # 5. Handle the File Transfer
        try:
            # First, receive the file name (e.g., "chunk_0.dat")
            file_name = client_socket.recv(1024).decode()
            
            # Send acknowledgement ("OK, send the data")
            client_socket.send(b"ACK")
            
            # Open file to write
            file_path = os.path.join(STORAGE_DIR, file_name)
            with open(file_path, "wb") as f:
                while True:
                    # Receive 1KB at a time
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    f.write(data)
            
            print(f"[+] Saved: {file_name}")
            
        except Exception as e:
            print(f"[-] Error: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    start_server()