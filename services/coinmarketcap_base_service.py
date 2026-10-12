import requests
from typing import Any
import os

BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency"


def get_cryptocurrency_data(
    path: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            BASE_URL + (path if path.startswith("/") else "/" + path),
            headers={"x-cmc_pro_api_key": os.getenv("COINMARKETCAP_API_KEY")},
            params=params,
        )

        response.raise_for_status()
        return response.json().get("data", [])
    except requests.RequestException as e:
        print(f"Error fetching cryptocurrency data: {e}")
        return []
