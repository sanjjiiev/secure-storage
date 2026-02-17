import os
import hashlib
from cryptography.fernet import Fernet

class FileHandler:
    def __init__(self):
        self.chunk_size = 1024 * 1024  # 1 MB chunks (Adjustable)

    # --- 1. SECURITY: Generate & Load Keys ---
    def generate_key(self):
        """Generates a key and saves it into a file"""
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
        return key

    def load_key(self):
        """Loads the key from the current directory"""
        return open("secret.key", "rb").read()

    # --- 2. ENCRYPTION: Lock the file ---
    def encrypt_file(self, filename, key):
        """Encrypts a file and returns the encrypted data"""
        f = Fernet(key)
        with open(filename, "rb") as file:
            file_data = file.read()
        
        encrypted_data = f.encrypt(file_data)
        
        # Save encrypted version locally (Simulating the 'Staging Area')
        enc_filename = filename + ".enc"
        with open(enc_filename, "wb") as file:
            file.write(encrypted_data)
            
        print(f"[SUCCESS] Encrypted '{filename}' -> '{enc_filename}'")
        return enc_filename

    # --- 3. SHARDING: Split the file ---
    def split_file(self, encrypted_filename):
        """Splits the encrypted file into smaller chunks"""
        chunks = []
        chunk_names = []
        
        with open(encrypted_filename, 'rb') as f:
            chunk_number = 0
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break
                
                # Name the chunk: file.enc_part_0, file.enc_part_1...
                chunk_name = f"{encrypted_filename}_part_{chunk_number}"
                
                # In a real app, we send these bytes to other PCs. 
                # For now, save them to disk to verify it works.
                with open(chunk_name, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)
                
                chunks.append(chunk_data)
                chunk_names.append(chunk_name)
                chunk_number += 1
        
        print(f"[SUCCESS] Split into {len(chunks)} chunks.")
        return chunks, chunk_names

    # --- 4. INTEGRITY: Build Merkle Tree ---
    def build_merkle_tree(self, chunks):
        """
        Takes a list of binary chunks and returns the Merkle Root Hash.
        This Root Hash is what gets stored on the Blockchain.
        """
        # Step A: Hash every chunk individually
        hashes = [hashlib.sha256(c).hexdigest() for c in chunks]
        
        # Step B: Combine hashes until we have one Root
        while len(hashes) > 1:
            temp_hashes = []
            
            # Process pairs (0,1), (2,3), etc.
            for i in range(0, len(hashes), 2):
                node1 = hashes[i]
                
                # If there is an odd number of items, duplicate the last one
                if i + 1 < len(hashes):
                    node2 = hashes[i+1]
                else:
                    node2 = node1 
                
                # Combine and Hash again
                combined = node1 + node2
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                temp_hashes.append(new_hash)
            
            hashes = temp_hashes
            
        merkle_root = hashes[0]
        print(f"[SUCCESS] Merkle Root Generated: {merkle_root}")
        return merkle_root

# --- TESTING IT OUT ---
if __name__ == "__main__":
    # 1. Create a dummy file to test
    with open("test_document.txt", "w") as f:
        f.write("This is a secret project file " * 50000) # Create a large text file

    handler = FileHandler()
    
    # 2. Generate a Key (Only need to do this once normally)
    key = handler.generate_key()
    
    # 3. Encrypt
    encrypted_file = handler.encrypt_file("test_document.txt", key)
    
    # 4. Split
    file_chunks, chunk_filenames = handler.split_file(encrypted_file)
    
    # 5. Merkle Root
    root_hash = handler.build_merkle_tree(file_chunks)
    
    print("\n--- SUMMARY ---")
    print(f"Original File: test_document.txt")
    print(f"Encrypted File: {encrypted_file}")
    print(f"Total Chunks: {len(chunk_filenames)}")
    print(f"Blockchain Entry (Merkle Root): {root_hash}")