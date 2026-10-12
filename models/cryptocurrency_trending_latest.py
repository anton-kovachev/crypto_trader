from dataclasses import dataclass
from typing import Any

from .crypto_currency_quote import CryptoCurrencyQuote
from .crypto_currency_platform import CryptoCurrencyPlatform


@dataclass
class CryptocurrencyTrendingLatest:
    id: int
    name: str
    symbol: str
    slug: str
    cmc_rank: int | None = None
    is_active: int | None = None
    is_fiat: int | None = None
    self_reported_circulating_supply: float | None = None
    self_reported_market_cap: float | None = None
    num_market_pairs: int | None = None
    circulating_supply: float | None = None
    total_supply: float | None = None
    max_supply: float | None = None
    last_updated: str | None = None
    date_added: str | None = None
    tags: list[str] | None = None
    platform: CryptoCurrencyPlatform | None = None
    quote: dict[str, CryptoCurrencyQuote] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CryptocurrencyTrendingLatest":
        return cls(
            id=data["id"],
            name=data["name"],
            symbol=data["symbol"],
            slug=data["slug"],
            cmc_rank=data.get("cmc_rank"),
            is_active=data.get("is_active"),
            is_fiat=data.get("is_fiat"),
            self_reported_circulating_supply=data.get(
                "self_reported_circulating_supply"
            ),
            self_reported_market_cap=data.get("self_reported_market_cap"),
            num_market_pairs=data.get("num_market_pairs"),
            circulating_supply=data.get("circulating_supply"),
            total_supply=data.get("total_supply"),
            max_supply=data.get("max_supply"),
            last_updated=data.get("last_updated"),
            date_added=data.get("date_added"),
            tags=data.get("tags"),
            platform=(
                CryptoCurrencyPlatform.from_dict(data["platform"])
                if data.get("platform")
                else None
            ),
            quote=(
                {
                    currency: CryptoCurrencyQuote.from_dict(quote_data)
                    for currency, quote_data in data["quote"].items()
                }
                if data.get("quote")
                else None
            ),
        )
