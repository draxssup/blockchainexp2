from flask import Flask, jsonify, request
from flask_ngrok import run_with_ngrok
import datetime
import hashlib
import json

class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []  # transaction pool
        self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions  # include txns
        }
        self.transactions = []  # clear transaction pool
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        while True:
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()
            ).hexdigest()
            if hash_operation[:3] == '000':  # Golden nonce condition
                return new_proof
            new_proof += 1

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        for block_index in range(1, len(chain)):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()
            ).hexdigest()
            if hash_operation[:3] != '000':
                return False
            previous_block = block
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

app = Flask(__name__)
run_with_ngrok(app)  # For running on Colab
blockchain = Blockchain()

@app.route('/mine_block', methods=['GET'])
def mine_block():
    if not blockchain.transactions:
        return jsonify({'message': 'No transactions to mine'}), 400
    
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Block successfully mined!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200

@app.route('/get_chain', methods=['GET'])
def get_chain():
    return jsonify({
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    return jsonify({'message': 'Blockchain is valid!' if valid else 'Blockchain is not valid!'}), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    required_fields = ['sender', 'receiver', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing fields in transaction'}), 400
    
    index = blockchain.add_transaction(data['sender'], data['receiver'], data['amount'])
    return jsonify({'message': f'This transaction will be added to Block {index}'}), 201

app.run()

