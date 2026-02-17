import json
import time
import hashlib

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        
        # Create the "Genesis Block" (The first block)
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """Creates a new Block and adds it to the chain"""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, owner, file_hash, file_name, chunks_metadata):
        """
        Creates a new transaction to go into the next Mined Block
        :param owner: Sender's Address (User ID)
        :param file_hash: The Merkle Root (File ID)
        :param file_name: Original filename
        :param chunks_metadata: Dictionary { "chunk_0": "192.168.1.5", "chunk_1": "192.168.1.6" }
        """
        self.current_transactions.append({
            'owner': owner,
            'file_hash': file_hash,
            'file_name': file_name,
            'locations': chunks_metadata,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """Hashes a Block (SHA-256)"""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]
    
    def get_file_location(self, file_hash):
        """Search the blockchain for a specific file"""
        for block in self.chain:
            for tx in block['transactions']:
                if tx['file_hash'] == file_hash:
                    return tx
        return None

# --- TESTING IT ---
if __name__ == "__main__":
    blockchain = Blockchain()
    
    # Simulate adding a file
    blockchain.new_transaction(
        owner="User_A",
        file_hash="abc123merkleRoot",
        file_name="secret.pdf",
        chunks_metadata={"chunk_0": "192.168.1.5", "chunk_1": "192.168.1.6"}
    )
    
    # Mine a block (Save it)
    blockchain.new_block(proof=12345)
    
    print("Blockchain Content:")
    print(json.dumps(blockchain.chain, indent=4))