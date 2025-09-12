# Module: gex
from urllib.parse import urlencode


def gamma_exposure(
    symbols: str = "AAPL",
    expirations=None,
    groupBy: str = "strikePrice",
    max_strike_spot_distance: int = 100,
) -> str:
    """URL builder for gamma_exposure"""
    base_url = "https://www.barchart.com/proxies/core-api/v1/options/get"
    params = {
        "symbols": symbols,
        "expirations": expirations,
        "groupBy": groupBy,
        f"le(nearestToLast,{max_strike_spot_distance})": "",
        "fields": "symbol,strikePrice,optionType,baseDailyLastPrice,baseLastPrice,dailyGamma,gamma,delta,dailyDelta,dailyOpenInterest,openInterest,dailyVolume,volume,daysToExpiration,expirationDate,averageVolatility",
    }
    query = urlencode(params)
    url = base_url + "?" + query
    return url
