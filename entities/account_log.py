from datetime import datetime, timezone
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
        raw_timestamp = data["datetime"]
        if isinstance(raw_timestamp, str):
            timestamp = datetime.fromisoformat(
                raw_timestamp.replace("Z", "+00:00")
            )
        elif isinstance(raw_timestamp, datetime):
            timestamp = raw_timestamp
        else:
            raise TypeError(
                "Account log datetime must be a datetime or ISO 8601 string"
            )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        return cls(
            name=data["name"],
            type=data["type"],
            message=data["message"],
            timestamp=timestamp,
        )
