from flask import Flask, request, jsonify
from blockchain import Blockchain
import time

app = Flask(__name__)
blockchain = Blockchain()


# The "Phonebook": Stores active nodes { "ip:port": timestamp }
active_nodes = {}

@app.route('/register', methods=['POST'])
def register():
    """Nodes call this to say 'I am here!'"""
    data = request.json
    node_address = f"{data['ip']}:{data['port']}"
    active_nodes[node_address] = time.time()
    print(f"[+] Node Registered: {node_address}")
    return jsonify({"status": "registered", "nodes": list(active_nodes.keys())})

@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    """Clients call this to find storage locations."""
    # Cleanup: Remove nodes inactive for more than 5 minutes
    current_time = time.time()
    dead_nodes = [node for node, last_seen in active_nodes.items() if current_time - last_seen > 300]
    for node in dead_nodes:
        del active_nodes[node]
        
    return jsonify(list(active_nodes.keys()))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    values = request.json
    
    # Check that the required fields are in the POST data
    required = ['owner', 'file_hash', 'file_name', 'locations']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['owner'], values['file_hash'], values['file_name'], values['locations'])
    
    # "Mine" the block immediately (Simulating Instant Consensus)
    blockchain.new_block(proof=100)
    
    response = {'message': f'Transaction added to Block {index}'}
    return jsonify(response), 201

@app.route('/get_file/<file_hash>', methods=['GET'])
def get_file(file_hash):
    """Retrieve file metadata (locations) from the Blockchain"""
    result = blockchain.get_file_location(file_hash)
    if result:
        return jsonify(result), 200
    else:
        return jsonify({"error": "File not found"}), 404
    
@app.route('/chain', methods=['GET'])
def full_chain():
    """Returns the full Blockchain Ledger"""
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    # Run on all interfaces, port 8000
    print("[*] Discovery Server running on port 8000...")
    app.run(host='0.0.0.0', port=8000)