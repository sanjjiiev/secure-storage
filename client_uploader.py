import socket
import os
import time

def send_chunk(target_ip, target_port, file_path):
    """
    Sends a single file to a specific Node (IP:Port).
    """
    if not os.path.exists(file_path):
        print(f"[-] File {file_path} not found.")
        return False

    try:
        print(f"[*] Connecting to {target_ip}:{target_port}...")
        
        # 1. Create Socket & Connect
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5) # 5 second timeout if node is dead
        s.connect((target_ip, target_port))
        
        # 2. Send Filename first
        filename = os.path.basename(file_path)
        s.send(filename.encode())
        
        # 3. Wait for "ACK" (Acknowledgement)
        ack = s.recv(1024)
        if ack != b"ACK":
            print("[-] Server did not acknowledge filename.")
            return False
            
        # 4. Send File Data
        with open(file_path, "rb") as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                s.send(data)
        
        print(f"[+] Uploaded {filename} to {target_ip}")
        s.close()
        return True

    except Exception as e:
        print(f"[-] Failed to send to {target_ip}: {e}")
        return False

# --- TEST SCENARIO ---
if __name__ == "__main__":
    # 1. Create a dummy chunk to send (Simulation)
    with open("chunk_test.dat", "w") as f:
        f.write("This is a distributed file chunk data " * 100)
    
    # 2. Define Target (Where is the storage node?)
    # IF TESTING ON SAME LAPTOP: Use '127.0.0.1' (Localhost)
    # IF TESTING ON 2 LAPTOPS: Use the IP of Laptop B (e.g., '192.168.1.5')
    TARGET_IP = '172.16.24.173' 
    TARGET_PORT = 5001
    
    send_chunk(TARGET_IP, TARGET_PORT, "chunk_test.dat")