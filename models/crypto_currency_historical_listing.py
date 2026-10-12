from dataclasses import dataclass
import decimal
from typing import Any

from .crypto_currency_platform import CryptoCurrencyPlatform
from .crypto_currency_quote import CryptoCurrencyQuote


@dataclass
class CryptoCurrencyHistoricalListing:
    id: int
    name: str
    symbol: str
    slug: str
    cmc_rank: int
    num_market_pairs: int
    circulating_supply: float
    infinite_supply: bool
    last_updated: str
    date_added: str
    tags: list[str]
    total_supply: float | None = None
    max_supply: float | None = None
    platform: CryptoCurrencyPlatform | None = None
    quote: dict[str, CryptoCurrencyQuote] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CryptoCurrencyHistoricalListing":
        return cls(
            id=data["id"],
            name=data["name"],
            symbol=data["symbol"],
            slug=data["slug"],
            cmc_rank=data["cmc_rank"],
            num_market_pairs=data["num_market_pairs"],
            circulating_supply=data["circulating_supply"],
            infinite_supply=data["infinite_supply"],
            last_updated=data["last_updated"],
            date_added=data["date_added"],
            tags=data["tags"],
            total_supply=data.get("total_supply"),
            max_supply=data.get("max_supply"),
            platform=(
                CryptoCurrencyPlatform.from_dict(data["platform"])
                if data.get("platform")
                else None
            ),
            quote=(
                {k: CryptoCurrencyQuote.from_dict(v) for k, v in data["quote"].items()}
                if data.get("quote")
                else None
            ),
        )
