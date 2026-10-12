from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class QuoteDict:
    chainId: int
    swapper: str
    tradeType: str
    route: list[list[dict[str, Any]]]
    input: dict[str, Any]
    output: dict[str, Any]


@dataclass
class QuoteResult:
    token_in: str
    token_out: str
    amount_in: str

    quote: QuoteDict
    raw_response: dict[str, Any]

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuoteResult":
        return cls(
            token_in=data["token_in"],
            token_out=data["token_out"],
            amount_in=data["amount_in"],
            quote=data.get("quote", {}),
            raw_response=data.get("raw_response", {}),
        )
