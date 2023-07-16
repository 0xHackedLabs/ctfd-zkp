from eth_utils import (
    to_hex, to_bytes,
    function_signature_to_4byte_selector,
    to_normalized_address
)
from eth_abi import decode, encode
from web3 import Web3


def eth_call(w3: Web3, to: str, sig: str, *args, block_number='latest'):
    res = w3.eth.call({
        'value': 0,
        'gas': 1_000_000,
        'to': to,
        'data': function_signature_to_4byte_selector(sig) + b''.join(args),
    }, block_number)
    return res


def check(info: dict, proof: dict):

    """
    proof: {
        "block_number": 1234,
        "deals": [{}],
        "asset_change": [
            {
                "address": "0x...",
                "token": "0x...", # zero means ETH
                "from": "0x...",
                "to": "0x...",
            }
        ],
        "state_diff": [
            "0x...": {
                "balance": "=",
                "nonce": {
                    "+": 1,
                },
                "code_hash": "=",
                "storage": {
                    "0x...": {
                        "*": {
                            "from": "0x...",
                            "to": "0x...",
                        }
                    },
                }
            }
        ],
    }
    """
    w3 = Web3(Web3.HTTPProvider(info['eth_rpc_url']))
    setup_contract = info['setup_contract']
    block_number = info['block_number']
    target_contract = eth_call(
        w3, setup_contract, "random()", block_number=block_number)
    target_contract = decode(['address'], target_contract)[0]

    flag_slot = to_hex(encode(['uint256'], [0]))
    flag_storage_diff = proof['state_diff'][target_contract]['storage'].get(flag_slot)
    try:
        slot_value = flag_storage_diff['*']['to']
        slot_value = decode(['bool'], to_bytes(hexstr=slot_value))[0]
        if slot_value == True:
            return True
    except:
        pass
    return False
