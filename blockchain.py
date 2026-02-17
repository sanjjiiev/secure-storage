import hashlib
import json
import time

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