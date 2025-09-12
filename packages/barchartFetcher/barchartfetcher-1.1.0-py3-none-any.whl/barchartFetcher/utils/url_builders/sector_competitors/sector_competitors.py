# Module: sector_competitors
from urllib.parse import urlencode


def sector_competitors(
    symbol: str = "AAPL",
    sector_symbol: str = "-COMC",
    orderBy: str = "weightedAlpha",
    orderDir: str = "desc",
    hasOptions: str = "true",
    page: int = 1,
    limit: int = 100,
    raw: int = 1,
) -> str:
    """URL builder for sector_competitors"""
    base_url = "https://www.barchart.com/proxies/core-api/v1/quotes/get"
    params = {
        "symbol": symbol,
        "lists": f"stocks.inSector.all({sector_symbol})",
        "orderBy": orderBy,
        "orderDir": orderDir,
        "hasOptions": hasOptions,
        "page": page,
        "limit": limit,
        "raw": raw,
        "fields": "symbol,weightedAlpha,lastPrice,priceChange,percentChange,highPrice1y,lowPrice1y,percentChange1y,tradeTime,symbolCode,symbolType,hasOptions",
        "meta": "field.shortName,field.type,field.description,lists.lastUpdate",
    }

    query = urlencode(params)
    url = base_url + "?" + query
    return url
