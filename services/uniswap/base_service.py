import requests
import os
from typing import Any
from config import UNISWAP_API_KEY
import json

BASE_URL = "https://trade-api.gateway.uniswap.org/v1"


def post_exchange_data(path: str, data: dict[str, Any]):
    url = f"{BASE_URL}/{path}"
    headers = {
        "x-api-key": UNISWAP_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-erc20eth-enabled": "true",
    }
    response = requests.post(url, json=convert_keys(data), headers=headers)
    response.raise_for_status()
    return response.json()


def snake_to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:] if p)


def convert_keys(obj):
    if isinstance(obj, dict):
        return {
            (snake_to_camel(k) if isinstance(k, str) else k): convert_keys(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [convert_keys(v) for v in obj]
    return obj
