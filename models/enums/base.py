from typing import Literal

SortDir = Literal["asc", "desc"]
CryptoCurrencyType = Literal["all", "coins", "tokens"]
Aux = Literal[
    "platform",
    "tags",
    "date_added",
    "circulating_supply",
    "total_supply",
    "max_supply",
    "cmc_rank",
    "num_market_pairs",
]
