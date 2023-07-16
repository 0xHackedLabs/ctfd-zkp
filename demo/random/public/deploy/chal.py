import json
from pathlib import Path
import time
from web3 import Web3
from web3.exceptions import TransactionNotFound


def send_transaction(web3, tx):
    if 'gas' not in tx:
        tx['gas'] = 10_000_000
    if 'gasPrice' not in tx:
        tx['gasPrice'] = 0
    
    txhash = web3.eth.send_transaction(tx)
    while True:
        try:
            receipt = web3.eth.get_transaction_receipt(txhash)
            break
        except TransactionNotFound:
            time.sleep(0.1)
    if receipt.status != 1:
        raise Exception("failed to send transaction")
    return receipt


def deploy(web3: Web3, deployer_address: str) -> str:
    rcpt = send_transaction(web3, {
        "from": deployer_address,
        "data": json.loads(Path("compiled/Setup.sol/Setup.json").read_text())["bytecode"]["object"],
    })
    return rcpt.contractAddress