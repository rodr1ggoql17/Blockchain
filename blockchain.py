from hashlib import sha256
import time
import json
from flask import Flask, request
import requests
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash


    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys = True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2
    def __init__(self):
        self.unconfirmed_transaction = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), '0'*64)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
        
    @property
    def last_block(self):
        return self.chain[-1]
    
    def print_block(self, n):
        if (len(self.chain) < n):
            return
        else:      
            block = self.chain[n]
            return ' Index {}\n Transactions {}\n Timestamp: {}\n PreviousHash: {}\n'.format(block.index, block.transactions, block.timestamp, block.previous_hash) 

    def proof_of_work(self,block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0'*Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash
    
    def add_block(self,block,proof):
        previous_hash = self.last_block.hash
        if(previous_hash != block.previous_hash):
            return False
        if not self.is_valid_proof(block, proof):
            return False
        block.hash = proof 
        self.chain. append(block)
        return True
    
    @classmethod
    def is_valid_proof(self,block, block_hash):
        return (block_hash.startswith('0'*Blockchain.difficulty) and block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls,chain):
        result = True
        previous_hash = "0"
        for block in chain:
            block_hash = block.hash
            delattr(block, "hash")
            if not cls.is_valid_proof(block, block.hash) or previous_hash != block.previous_hash:
                result = False
                break
            block.hash, previous_hash = block_hash, block_hash
        return result
    def new_transaction(self, transaction):
        self.unconfirmed_transaction.append(transaction)
    
    def mine(self):
        if not self.unconfirmed_transaction:
            return False
        last_block = self.last_block
        new_block = Block(index=last_block.index-1, transactions= self.unconfirmed_transaction, timestamp= time.time(), previous_hash=last_block.hash)
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transaction = []
        return new_block.index

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    require_fields = ["author","content"]
    for field in require_fields:
        if not tx_data.get(field):
            return "Datos de transaccion invalidos ", 404
    tx_data["timestap"] = time.time()
    blockchain.new_transaction(tx_data)
    return "Exito", 201

@app.route('/chain',methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
        return json.dumps({"length":len(chain_data),
                           "chain":chain_data})

@app.route('/mine',methods = ['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result :
        return "No hay nada para minar"
    return "Block #{} fue minado".format(result)

@app.route('/pending_tx', methods = ['POST'])
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transaction)

app.run(port = 8000)
