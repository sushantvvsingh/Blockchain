# module 1 - create blockchain
import datetime as dt
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


#creating blockchain
class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.mempool = []
        self.mempoolLastUpdated = None
        #creating Genesis Block
        self.CreateBlock(proof = 1, previousHash = '0')
        self.nodes = set()
        
    def CreateBlock(self, proof, previousHash):
        block = {'index' : len(self.chain)+1,
                 'timestamp' : str(dt.datetime.now()),
                 'proof': proof,
                 'previousHash' : previousHash,
                 'transactions' : self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    def GetLastBlock(self):
        return self.chain[-1]
    
    def ProofOfWork(self, previousProof):
        newProof = 1
        proofFound = False
        while proofFound is False:
            newHash = hashlib.sha256(str(newProof**2 - previousProof**2).encode()).hexdigest()
            if newHash[:4] == '0000':
                proofFound = True
            else:
                newProof += 1
        return newProof
    
    def Hash(self,block):
        blockHash = hashlib.sha256(json.dumps(block,sort_keys = True).encode()).hexdigest()
        return blockHash
    
    def IsChainValid(self, chain):
        previousBlock = chain[0]
        currentBlockIndex = 1
        while currentBlockIndex < len(chain):
            currentBlock = chain[currentBlockIndex]
            if currentBlock['previousHash'] != self.hash(previousBlock):
                return False
            currentBlockProof = currentBlock['proof']
            previousBlockProof = previousBlock['proof']
            newHash = hashlib.sha256(str(currentBlockProof**2 - previousBlockProof**2).encode()).hexdigest()
            if newHash[:4] == '0000':
                return False
            previousBlock = currentBlock
            currentBlockIndex += 1
        return True
    
    def AddTransaction(self, sender, reciever, amount):
        self.transactions.append({'sender' : sender,
                                  'reciever' : reciever,
                                  'amount' : amount})
        previousBlock = self.GetLastBlock()
        return previousBlock['index'] + 1
    
    def AddNode(self, address):
        self.nodes.add(urlparse(address).netloc)
        
    def ReplaceChain(self):
        currentChainLength = len(self.chain)
        longestChain = None
        for node in self.nodes:
            if(nodeIp not in node):
                response = requests.get(f'http://{node}/getChain')
                if response.status_code == 200:
                    nodeChain = response.json()['chain']
                    nodeChainLength = response.json()['length']
                    if nodeChainLength > currentChainLength and self.IsChainValid(nodeChain):
                        currentChainLength = nodeChainLength
                        longestChain = nodeChain
        if longestChain:
            self.chain = longestChain
            return True
        return False
    
    def UpdateMempool(self):
        for node in self.nodes:
            if(nodeIp not in node):
                response = requests.get(f'http://{node}/getMempool')
                if response.status_code == 200:
                    lastUpdationTime = response.json()['lastUpdated']
                    nodeMempool = response.json()['mempool']
                    if lastUpdationTime > self.mempoolLastUpdated:
                        self.mempoolLastUpdated = lastUpdationTime
                        self.mempool = nodeMempool
                    
    
    def SendRequestToUpdateMempool(self):
        for node in self.nodes:
            if(nodeIp not in node):
                requests.get(f'http://{node}/updateMempool')
        
#mining 
        
app = Flask(__name__)
#app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

nodeAddress = str(uuid4()).replace('-','')
nodeIp = requests.get('http://ip.42.pl/raw').text

blockchain = Blockchain()

@app.route('/mineBlock', methods=['GET'])
def MineBlock():
    previousBlock = blockchain.GetLastBlock()
    previousProof = previousBlock['proof']
    currentProof = blockchain.ProofOfWork(previousProof)
    previousHash = blockchain.Hash(previousBlock)
    blockchain.AddTransaction(sender = nodeAddress, reciever = 'Me', amount = 1)
    block = blockchain.CreateBlock(currentProof,previousHash)
    blockchain.ReplaceChain()
    blockchain.SendRequestToUpdateMempool()
    response = {'message' : 'Block mined succesfully !!!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof': block['proof'],
                'previousHash' : block['previousHash'],
                'transactions' : block['transactions']}
    return jsonify(response), 200



@app.route('/getChain', methods=['GET'])
def GetChain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/isChainValid', methods=['GET'])
def IsChainValid():
    isChainValid = blockchain.IsChainValid(blockchain.chain)
    response = {'message' : 'Blockchain is Valid' if isChainValid else 'Blockchain is not valid'}
    return jsonify(response), 200

@app.route('/addTransaction', methods=['POST'])
def AddTransaction():
    blockchain.mempoolLastUpdated = str(dt.datetime.now())
    json = request.get_json()
    transactionKeys = ['sender', 'reciever', 'amount']
    if not all (key in json for key in transactionKeys):
        return 'Some fields are missing', 400
    index = blockchain.AddTransaction(json['sender'], json['reciever'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/addNode', methods=['POST'])
def AddNode():
    json = request.get_json()
    address = json.get('address')
    response = requests.get(f'http://{address}/getNodes')
    nodes = response.json()['nodes']
    if nodes in None:
        return "No node", 400
    for node in nodes:
        blockchain.AddNode(node)
    blockchain.ReplaceChain()
    response = {'message': 'All the nodes are now connected. The Sushicoin Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes),
                'chain' : blockchain.chain}
    return jsonify(response), 201

@app.route('/replaceChain', methods=['GET'])
def ReplaceChain():
    isChainReplaced = blockchain.ReplaceChain()
    response = {'message' : 'Chain is replaced' if isChainReplaced else 'Chain is not replaced',
                'chain' : blockchain.chain}
    return jsonify(response), 200

@app.route('/getNodes', methods=['GET'])
def GetNodes():
    response = {'nodes' : blockchain.nodes}
    return jsonify(response), 200

@app.route('/getMempool', methods=['GET'])
def GetMempool():
    response = {'mempool' : blockchain.mempool,
                'lastUpdated' : blockchain.mempoolLastUpdated}
    return jsonify(response), 200

@app.route('/updateMempool', methods=['GET'])
def UpdatetMempool():
    blockchain.UpdateMempool()
    response = {'message' : 'mempool updated',
                'mempool' : blockchain.mempool}
    return jsonify(response), 200

app.run(host = '0.0.0.0', port = 5000)





