from dataclasses import dataclass


@dataclass
class CryptoCurrencyQuote:
    price: float | None = None
    volume_24h: float | None = None
    volume_change_24h: float | None = None
    percent_change_1h: float | None = None
    percent_change_24h: float | None = None
    percent_change_7d: float | None = None
    percent_change_30d: float | None = None
    market_cap: float | None = None
    market_cap_dominance: float | None = None
    fully_diluted_market_cap: float | None = None
    last_updated: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "CryptoCurrencyQuote":
        return cls(
            price=data.get("price"),
            volume_24h=data.get("volume_24h"),
            volume_change_24h=data.get("volume_change_24h"),
            percent_change_1h=data.get("percent_change_1h"),
            percent_change_24h=data.get("percent_change_24h"),
            percent_change_7d=data.get("percent_change_7d"),
            percent_change_30d=data.get("percent_change_30d"),
            market_cap=data.get("market_cap"),
            market_cap_dominance=data.get("market_cap_dominance"),
            fully_diluted_market_cap=data.get("fully_diluted_market_cap"),
            last_updated=data.get("last_updated"),
        )
