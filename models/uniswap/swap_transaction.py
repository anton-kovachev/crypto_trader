from dataclasses import dataclass


@dataclass
class SwapTransaction:
    """
    Represents a Uniswap swap transaction.
    Contains all necessary fields for executing a swap on the Uniswap protocol.
    Attributes:
        to (str): The recipient address of the swap transaction.
        data (str): The calldata for the swap transaction.
        value (int): The amount of ETH to send with the transaction.
        gas (int): The gas limit for the transaction.
        nonce (int): The nonce for the transaction.
        permit_signature (str): The permit signature for the swap transaction.
    """

    to: str
    data: str
    value: int
    gas: int
    nonce: int
    permit_signature: str

    @classmethod
    def from_dict(cls, data: dict) -> "SwapTransaction":
        return cls(
            to=data.get("to", ""),
            data=data.get("data", ""),
            value=int(data.get("value", 0)),
            gas=int(data.get("gas", 0)),
            nonce=int(data.get("nonce", 0)),
            permit_signature=data.get("permitSignature", ""),
        )
