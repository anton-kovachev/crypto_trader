from datetime import datetime
from typing import Any
from dataclasses import dataclass


@dataclass
class AccountLog:
    name: str
    type: str
    message: str
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountLog":
        return cls(
            name=data["name"],
            type=data["type"],
            message=data["message"],
            timestamp=data["datetime"],
        )
