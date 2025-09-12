# Module: options_prices
from urllib.parse import urlencode


def options_prices(
    baseSymbol: str = "AAPL",
    groupBy: str = "optionType",
    expirationDate=None,
    orderBy: str = "strikePrice",
    orderDir: str = "asc",
    optionsOverview: str = "true",
    raw: int = 1,
) -> str:
    """URL builder for options_prices"""
    base_url = "https://www.barchart.com/proxies/core-api/v1/options/get"
    params = {
        "baseSymbol": baseSymbol,
        "groupBy": groupBy,
        "orderBy": orderBy,
        "orderDir": orderDir,
        "optionsOverview": optionsOverview,
        "raw": raw,
        "fields": "symbol,baseSymbol,strikePrice,expirationDate,moneyness,bidPrice,midpoint,askPrice,lastPrice,priceChange,percentChange,volume,openInterest,openInterestChange,delta,volatility,optionType,daysToExpiration,tradeTime,averageVolatility,historicVolatility30d,baseNextEarningsDate,dividendExDate,baseTimeCode,impliedVolatilityRank1y,symbolCode,symbolType,theoretical,gamma,theta,vega,rho,volumeOpenInterestRatio,itmProbabilityexpirationType,expiration,dte,bidXSize,askXSize,tradePrice,tradeSize,side,premium,tradeCondition,label,baseSymbolType",
        "meta": "field.shortName,field.description,field.type",
    }
    if expirationDate:
        params["expirationDate"] = expirationDate

    query = urlencode(params)
    url = base_url + "?" + query
    return url
