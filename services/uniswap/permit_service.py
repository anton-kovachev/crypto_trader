from eth_account import Account
from eth_account.messages import encode_typed_data

from config import CHAIN_ID


def build_permit2_signature(
    private_key: str,
    token: str,
    amount: int,
    nonce: int,
    expiration: int,
    permit2_address: str,
    spender: str,
) -> str:
    domain = {
        "name": "Permit2",
        "version": "1",
        "chainId": CHAIN_ID,
        "verifyingContract": permit2_address,
    }

    types = {
        "PermitSingle": [
            {"name": "details", "type": "PermitDetails"},
            {"name": "spender", "type": "address"},
            {"name": "sigDeadline", "type": "uint256"},
        ],
        "PermitDetails": [
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint160"},
            {"name": "expiration", "type": "uint48"},
            {"name": "nonce", "type": "uint48"},
        ],
    }

    message = {
        "details": {
            "token": token,
            "amount": amount,
            "expiration": expiration,
            "nonce": nonce,
        },
        "spender": spender,
        "sigDeadline": expiration,
    }

    signed = Account.sign_message(
        encode_typed_data(
            {
                "types": types,
                "primaryType": "PermitSingle",
                "domain": domain,
                "message": message,
            }
        ),
        private_key,
    )

    return signed.signature.hex()
