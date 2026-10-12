from dataclasses import dataclass
from typing import Any
from .crypto_currency_platform import CryptoCurrencyPlatform


@dataclass
class CryptocurrencyMap:
    id: int
    name: str
    symbol: str
    slug: str
    rank: int | None
    is_active: int
    first_historical_data: str | None = None
    last_historical_data: str | None = None
    platform: CryptoCurrencyPlatform | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "CryptocurrencyMap":
        return cls(
            id=data["id"],
            rank=data.get("rank"),
            name=data["name"],
            symbol=data["symbol"],
            slug=data["slug"],
            is_active=data["is_active"],
            first_historical_data=data.get("first_historical_data"),
            last_historical_data=data.get("last_historical_data"),
            platform=(
                CryptoCurrencyPlatform.from_dict(data["platform"])
                if data.get("platform")
                else None
            ),
        )
