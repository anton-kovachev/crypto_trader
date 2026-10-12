from typing import Literal

from mcp.server import FastMCP
from models import (
    CryptoCurrencyHistoricalListing,
    CryptocurrencyMap,
    CryptocurrencyTrendingLatest,
)
from models.enums.base import CryptoCurrencyType, SortDir
from models.enums.crypto_currency_historical_listing import (
    CryptoCurrencyHistoricalListingSort,
)
from services import (
    get_cryptocurrency_map,
    get_current_cryptocurrency_listings,
    get_historical_listings,
)

mcp = FastMCP("coinmarketcap_data_server")


@mcp.tool()
def get_cryptocurrency_data(
    symbol: str,
    start: int = 1,
    limit: int = 100,
    sort: Literal["id", "cmc_rank"] = "id",
) -> list[CryptocurrencyMap]:
    """
    Return CoinMarketCap cryptocurrency records mapped to unique CMC IDs.

    Each record includes identifiers such as name, symbol, and token address,
    plus the first and last available historical-data timestamps. CMC IDs are
    recommended for reliably identifying cryptocurrencies in API requests and
    application logic.

    Args:
        symbol: Required comma-separated ticker symbol(s) (e.g. "BNB" or
            "BTC,ETH") to filter results. Always pass this when looking up a
            specific coin instead of fetching the full list, which is very
            large and can exceed the model's context window.
        start: The starting index for the results (default is 1).
        limit: The maximum number of results to return (default is 100).
        sort: The field by which to sort the results (default is "id").

    Returns:
        list[CryptocurrencyMap]: A list of cryptocurrency records. Each record
        contains the unique CoinMarketCap ID, current rank, name, symbol, slug,
        and active-status flag. It also includes the first and last available
        historical-data timestamps and platform information when available.
    """
    return get_cryptocurrency_map(symbol=symbol, start=start, limit=limit, sort=sort)


@mcp.tool()
def get_current_cryptocurrency_data(
    start: int = 1,
    limit: int = 100,
    time_period: Literal["24h", "7d", "30d"] = "24h",
    convert: str | None = None,
    convert_id: str | None = None,
) -> list[CryptocurrencyTrendingLatest]:
    """
    Returns latest and recent (up to 30 days) pricing for Cryptocurrencies from CoinMarketCap as a list
    of CryptocurrencyTrendingLatest records and their price changes over the specified time period.

    Each record includes the cryptocurrency's CoinMarketCap ID, name, symbol,
    slug, and optional rank and status flags. It may also include market-pair
    count, circulating, total, maximum, and self-reported supply and market-cap
    values, along with the date added and last-updated timestamp. Tags,
    platform details, and quote-specific market data are returned when
    available. Fields other than ID, name, symbol, and slug may be null.
    This tool should be used to fetch current and historical pricing for cryptocurrencies like ETH/BTC and ETH/USDC from CoinMarketCap up to 30 days in the past.

    Args:
        start: The starting index for the results (default is 1).
        limit: The maximum number of results to return (default is 100).
        time_period: The time period for trending data (default is "24h").
        convert: The currency to convert the market data into (optional) (e.g. "BNB" to get the price of 120 crypto currencies in BNB i.e. BNB price in BTC, BNB price in ETH, etc...).
        convert_id: The CoinMarketCap ID of the currency to convert the market data into, same as the convert parameter but with an id instead of a symbol (optional) (e.g. "1,2781").

    Returns:
        list[CryptocurrencyTrendingLatest]: Latest trending cryptocurrency
        records with identity, ranking, supply, metadata, and quote data.
    """
    return get_current_cryptocurrency_listings(
        start=start,
        limit=limit,
        time_period=time_period,
        convert=convert,
        convert_id=convert_id,
    )


@mcp.tool()
def get_historical_cryptocurrency_data(
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
    """
    Returns a ranked and sorted historical pricing listings from one month to about an year in the past of cryptocurrencies from CoinMarketCap
    for a historical UTC date as a list of CryptoCurrencyHistoricalListing records.
    For precise pricing data between different token pairs that is older than 30 days, use this tool.
    This endpoint is identical in format to our /cryptocurrency/listings/latest endpoint
    but is used to retrieve historical daily ranking snapshots from the end of each UTC day.
    The required "date" parameter can be passed as a Unix timestamp or ISO 8601 date but only the date portion of the timestamp will be referenced.
    It is recommended to send an ISO date format like "2019-10-10" without time.
    This tool should be used to fetch historical pricing for cryptocurrencies like ETH/BTC and ETH/USDC from CoinMarketCap from 30 days ago up to 1 year in the past.

    Each record includes the cryptocurrency's CoinMarketCap ID, name, symbol,
    slug, and optional rank and status flags. It may also include market-pair
    count, circulating, total, maximum, and self-reported supply and market-cap
    values, along with the date added and last-updated timestamp. Tags,
    platform details, and quote-specific market data are returned when
    available. Fields other than ID, name, symbol, and slug may be null.

    Args:
        date: The date for historical listings in YYYY-MM-DD format.
        start: The starting index for the results (default is 0).
        limit: The maximum number of results to return (default is 100).
        convert: The currency to convert the market data into (optional).
        convert_id: The CoinMarketCap ID of the currency to convert the market data into (optional).
        sort: The field to sort the results by (default is "cmc_rank").
        sort_dir: The order to sort the results in (default is "asc").
        cryptocurrency_type: The type of cryptocurrency to include (default is "all").
        aux: Additional fields to include in the response (optional).

    Returns:
        list[CryptoCurrencyHistoricalListing]: Historical cryptocurrency listings
        with identity, ranking, supply, metadata, and quote data.
    """
    return get_historical_listings(
        date=date,
        start=start,
        limit=limit,
        convert=convert,
        convert_id=convert_id,
        sort=sort,
        sort_dir=sort_dir,
        cryptocurrency_type=cryptocurrency_type,
        aux=aux,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
