import requests
from typing import Any

from config import UNISWAP_API_KEY, UNISWAP_QUOTE_URL, CHAIN_ID, USER_ADDRESS
from models import QuoteRequest, QuoteResult
from .base_service import post_exchange_data


def get_quote(token_in: str, token_out: str, amount: str) -> QuoteResult:

    payload: QuoteRequest = QuoteRequest(
        type="EXACT_INPUT",
        amount=amount,
        token_in_chain_id=CHAIN_ID,
        token_out_chain_id=CHAIN_ID,
        token_in=token_in,
        token_out=token_out,
        swapper=USER_ADDRESS,
        slippage_tolerance=0.5,
    )

    data = post_exchange_data("quote", payload.to_dict())
    return QuoteResult(
        token_in=token_in,
        token_out=token_out,
        amount_in=amount,
        quote=data.get("quote", {}),
        raw_response=data,
    )
