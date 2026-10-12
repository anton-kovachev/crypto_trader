from dataclasses import dataclass, asdict


@dataclass
class QuoteRequest:
    type: str
    amount: str
    token_in_chain_id: int
    token_out_chain_id: int
    token_in: str
    token_out: str
    swapper: str
    slippage_tolerance: float

    def to_dict(self):
        return asdict(self)
