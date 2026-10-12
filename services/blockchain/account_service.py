import os
from web3 import Web3
from config import CHAIN_RPC_URL


def get_account_nonce(account_address) -> int:
    w3 = Web3(Web3.HTTPProvider(CHAIN_RPC_URL))
    nonce = w3.eth.get_transaction_count(account_address, "pending")
    return nonce


def get_suggested_gas_price() -> int:
    w3 = Web3(Web3.HTTPProvider(CHAIN_RPC_URL))
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas")
    max_priority_fee = w3.eth.max_priority_fee

    if base_fee is not None:
        return base_fee + max_priority_fee
    else:
        return w3.eth.gas_price
