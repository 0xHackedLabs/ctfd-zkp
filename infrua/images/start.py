import os
import random
import socket
import subprocess
import signal
import sys
from threading import Thread
from typing import Dict, Tuple
import json
import time
from web3 import Web3
import aiohttp
from fastapi import FastAPI
import uvicorn
from eth_account import Account
from eth_account.hdaccount import generate_mnemonic


HTTP_PORT = int(os.getenv("HTTP_PORT", "8545"))
ETH_RPC_URL = os.getenv("ETH_RPC_URL", "https://rpc.flashbots.net")
ETH_BLOCK = os.getenv("ETH_BLOCK")
PUBLIC_IP = os.getenv("PUBLIC_IP", "127.0.0.1")
LOCAL_RPC_PORT = 8546

Account.enable_unaudited_hdwallet_features()


def launch_node(port: int, rpc_url: str, block_number: int = None) -> Dict:
    mnemonic = generate_mnemonic(12, "english")
    
    args = [
        "/root/.foundry/bin/anvil",
        "--accounts",
        "2",
        "--mnemonic",
        mnemonic,
        "--port",
        str(port),
        "--fork-url",
        rpc_url,
    ]
    if block_number is not None:
        args.extend(["--fork-block-number", str(block_number)])

    proc = subprocess.Popen(
        args=[
            "/root/.foundry/bin/anvil",
            "--accounts",
            "2",  # first account is the deployer
            "--balance",
            "5000",
            "--mnemonic",
            mnemonic,
            "--port",
            str(port),
            "--fork-url",
            ETH_RPC_URL,
            "--block-base-fee-per-gas",
            "0",
        ],
    )

    web3 = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{port}"))
    while True:
        if proc.poll() is not None:
            return None
        if web3.is_connected():
            break
        time.sleep(0.1)

    node_info = {
        "port": port,
        "mnemonic": mnemonic,
        "pid": proc.pid,
    }

    return node_info


app = FastAPI()

ALLOWED_NAMESPACES = ["web3", "eth", "net"]


@app.post("/")
async def proxy(body: dict):
    if "method" not in body or not isinstance(body["method"], str):
        return {
            "jsonrpc": "2.0",
            "id": body["id"],
            "error": {
                "code": -32600,
                "message": "invalid request",
            },
        }
    ok = (
        any(body["method"].startswith(namespace) for namespace in ALLOWED_NAMESPACES)
        and body["method"] != "eth_sendUnsignedTransaction"
    )
    if not ok:
        return {
            "jsonrpc": "2.0",
            "id": body["id"],
            "error": {
                "code": -32600,
                "message": "invalid request",
            },
        }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://127.0.0.1:{LOCAL_RPC_PORT}", json=body) as resp:
            data = await resp.json()
            return data



def main():
    node = launch_node(LOCAL_RPC_PORT, ETH_RPC_URL, ETH_BLOCK)
    mnemonic = node["mnemonic"]
        
    deployer_acct = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/0")
    web3 = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{node['port']}"))

    try:
        import chal
        setup_addr = chal.deploy(web3, deployer_acct.address)
    except Exception as e:
        print(f"failed to deploy contract: {e}")
        return

    print()
    print(f"your private blockchain has been deployed")
    print(f"here's some useful information")
    print(f"rpc endpoint:   http://{PUBLIC_IP}:{HTTP_PORT}")
    print(f"setup contract: {setup_addr}")
    print(f"block_number: {web3.eth.block_number}")
    print(flush=True)

    uvicorn.run("start:app", host="0.0.0.0", port=HTTP_PORT)


if __name__ == '__main__':
    main()
