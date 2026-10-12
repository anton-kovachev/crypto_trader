from dataclasses import dataclass


@dataclass
class SwapTransaction:
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
