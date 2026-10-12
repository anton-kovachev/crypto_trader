from dataclasses import dataclass


@dataclass
class CryptoCurrencyPlatform:
    id: int
    name: str | None = None
    symbol: str | None = None
    slug: str | None = None
    token_address: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "CryptoCurrencyPlatform":
        return cls(
            id=data["id"],
            name=data["name"],
            symbol=data["symbol"],
            slug=data["slug"],
            token_address=data["token_address"],
        )
