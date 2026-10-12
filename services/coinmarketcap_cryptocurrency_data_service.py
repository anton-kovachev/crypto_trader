import os
import requests
from typing import Any
from dotenv import load_dotenv
from models import (
    CryptocurrencyMap,
    CryptocurrencyTrendingLatest,
    CryptoCurrencyHistoricalListingSort,
    CryptoCurrencyHistoricalListing,
    SortDir,
    CryptoCurrencyType,
    Aux,
)
from app_logging.logger import log_and_raise
from .coinmarketcap_base_service import get_cryptocurrency_data, BASE_URL

load_dotenv(override=True)


@log_and_raise("Error occurred in get_cryptocurrency_map")
def get_cryptocurrency_map(
    symbol: str | None = None, start: int = 0, limit: int = 100, sort: str = "id"
) -> list[CryptocurrencyMap]:
    params = (
        {"symbol": symbol, "start": start, "limit": limit, "sort": sort}
        if symbol
        else {"start": start, "limit": limit, "sort": sort}
    )
    data = get_cryptocurrency_data("/map", params=params)
    return [CryptocurrencyMap.from_dict(item) for item in data]


@log_and_raise("Error occurred in get_current_cryptocurrency_listings")
def get_current_cryptocurrency_listings(
    start: int = 1,
    limit: int = 100,
    time_period: str = "24h",
    convert: str | None = None,
    convert_id: str | None = None,
) -> list[CryptocurrencyTrendingLatest]:
    params = {
        "start": start,
        "limit": limit,
        "time_period": time_period,
        "convert": convert,
        "convert_id": convert_id,
    }
    data = get_cryptocurrency_data("/listings/latest", params=params)
    return [CryptocurrencyTrendingLatest.from_dict(item) for item in data]


@log_and_raise("Error occurred in get_historical_listings")
def get_historical_listings(
    date: str,
    start: int = 1,
    limit: int = 100,
    convert: str | None = None,
    convert_id: str | None = None,
    sort: CryptoCurrencyHistoricalListingSort = "cmc_rank",
    sort_dir: SortDir = "asc",
    cryptocurrency_type: CryptoCurrencyType = "all",
    aux: str | None = None,
) -> list[CryptoCurrencyHistoricalListing]:
    params = {
        "date": date,
        "start": start,
        "limit": limit,
        "convert": convert,
        "convert_id": convert_id,
        "sort": sort,
        "sort_dir": sort_dir,
        "cryptocurrency_type": cryptocurrency_type,
        "aux": aux,
    }
    data = get_cryptocurrency_data("/listings/historical", params=params)
    return [CryptoCurrencyHistoricalListing.from_dict(item) for item in data]
