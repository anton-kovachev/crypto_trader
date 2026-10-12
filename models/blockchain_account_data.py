from dataclasses import dataclass


@dataclass
class BlockchainAccountData:
    account_address: str
    account_private_key: str
    chain_name: str
    chain_rpc_url: str
    chain_id: int
