import os
from web3 import Web3
from typing import Any

from config import CHAIN_RPC_URL, USER_PRIVATE_KEY
from models import SwapTransaction
from numpy import uint
import json


def submit_swap_transaction(tx: SwapTransaction) -> dict[str, Any]:
    w3 = Web3(Web3.HTTPProvider(CHAIN_RPC_URL))
    account = w3.eth.account.from_key(USER_PRIVATE_KEY)
    transaction = {
        "to": tx.to,
        "data": tx.data,
        "value": tx.value,
        "gas": tx.gas,
    }

    if tx.permit_signature:
        transaction["permitSignature"] = tx.permit_signature

    # signed_tx = account.sign_transaction(transaction)
    payload = json.dumps(transaction, sort_keys=True, separators=(",", ":"))
    digest = w3.keccak(text=payload)  # returns bytes

    tx_hash = str(digest)
    # if os.getenv("IS_LIVE", "false").lower() == "true":
    #     tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return {**transaction, "tx_hash": tx_hash}


def check_allowance(token: str, owner: str, spender: str, amount_to_spend: int) -> bool:
    return True


def allow(token: str, owner: str, spender: str, amount_to_approve: int) -> bool:
    return True
