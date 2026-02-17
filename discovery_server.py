from flask import Flask, request, jsonify
import time

app = Flask(__name__)

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

if __name__ == '__main__':
    # Run on all interfaces, port 8000
    print("[*] Discovery Server running on port 8000...")
    app.run(host='0.0.0.0', port=8000)