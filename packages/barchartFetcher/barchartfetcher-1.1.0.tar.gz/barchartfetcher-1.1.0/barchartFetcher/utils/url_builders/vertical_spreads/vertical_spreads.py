# Module: vertical_spreads
from urllib.parse import urlencode


def bear_call_spreads(
    baseSymbol: str = "AAPL",
    abs_deltaLeg1_low: int | float = 0,
    abs_deltaLeg1_high: int | float = 0.6,
    abs_deltaLeg2_low: str = "",
    abs_deltaLeg2_high: int | float = 0.3,
    riskRewardRatio_low: int | float = 2,
    riskRewardRatio_high: int | float = 5,
    orderBy: str = "strikeLeg1",
    orderDir: str = "desc",
    expirationDate=None,
    expirationType=None,
    raw: int = 1,
) -> str:
    """URL builder for bear_call_spreads"""
    base_url = "https://www.barchart.com/proxies/core-api/v1/options/bear-calls-spread"
    params = {
        f"between(abs(deltaLeg1),{abs_deltaLeg1_low},{abs_deltaLeg1_high})": "",
        f"between(abs(deltaLeg2),{abs_deltaLeg2_low},{abs_deltaLeg2_high})": "",
        f"between(riskRewardRatio,{riskRewardRatio_low},{riskRewardRatio_high})": "",
        "baseSymbol": baseSymbol,
        "orderBy": orderBy,
        "orderDir": orderDir,
        "raw": raw,
        "fields": "baseSymbol,underlyingLastPrice,expirationDate,daysToExpiration,strikeLeg1,bidPriceLeg1,strikeLeg2,askPriceLeg2,breakEven,breakEvenPercent,maxProfit,maxLoss,maxProfitPercent,riskRewardRatio,impliedVolatilityRank1y,lossProbability,time,averageVolatility,baseNextEarningsDate,timeCode,dividendExDate,historicVolatility30d,impliedVolatilityRank1y,baseTrendSpotterSignal,baseTrendSpotterStrength,symbolCode,symbolType",
        "meta": "expirations,field.shortName,field.type,field.description",
    }
    if expirationDate:
        params["expirationDate"] = expirationDate
    if expirationType:
        params["expirationType"] = expirationType

    query = urlencode(params)
    url = base_url + "?" + query
    return url


def bear_put_spreads(
    baseSymbol: str = "AAPL",
    riskRewardRatio_low: int | float = 0.33,
    riskRewardRatio_high: int | float = 1.5,
    orderBy: str = "strikeLeg1",
    orderDir: str = "desc",
    expirationDate=None,
    expirationType=None,
    raw: int = 1,
) -> str:
    """URL builder for bear_put_spreads"""
    base_url = (
        "https://www.barchart.com/proxies/core-api/v1/options/bear-puts-spread"
    )
    params = {
        f"between(riskRewardRatio,{riskRewardRatio_low},{riskRewardRatio_high})": "",
        "baseSymbol": baseSymbol,
        "orderBy": orderBy,
        "orderDir": orderDir,
        "between(abs(deltaLeg1),0.3,)": "",
        "between(abs(deltaLeg2),0.1,)": "",
        "raw": raw,
        "fields": "baseSymbol,underlyingLastPrice,expirationDate,daysToExpiration,strikeLeg1,askPriceLeg1,strikeLeg2,bidPriceLeg2,breakEven,breakEvenPercent,maxProfit,maxLoss,maxProfitPercent,riskRewardRatio,impliedVolatilityRank1y,breakEvenProbability,time,averageVolatility,baseNextEarningsDate,timeCode,dividendExDate,historicVolatility30d,impliedVolatilityRank1y,baseTrendSpotterSignal,baseTrendSpotterStrength,symbolCode,symbolType",
        "meta": "expirations,field.shortName,field.type,field.description",
    }
    if expirationDate:
        params["expirationDate"] = expirationDate
    if expirationType:
        params["expirationType"] = expirationType

    query = urlencode(params)
    url = base_url + "?" + query
    return url


def bull_call_spreads(
    baseSymbol: str = "AAPL",
    riskRewardRatio_low: int | float = 0.33,
    riskRewardRatio_high: int | float = 1.5,
    orderBy: str = "strikeLeg1",
    orderDir: str = "asc",
    expirationDate=None,
    expirationType=None,
    raw: int = 1,
) -> str:
    """URL builder for bull_call_spreads"""
    base_url = "https://www.barchart.com/proxies/core-api/v1/options/bull-calls-spread"
    params = {
        f"between(riskRewardRatio,{riskRewardRatio_low},{riskRewardRatio_high})": "",
        "baseSymbol": baseSymbol,
        "orderBy": orderBy,
        "orderDir": orderDir,
        "between(abs(deltaLeg1),0.3,)": "",
        "between(abs(deltaLeg2),0.1,)": "",
        "raw": raw,
        "fields": "baseSymbol,breakEven,breakEvenPercent,maxProfit,maxLoss,maxProfitPercent,riskRewardRatio,impliedVolatilityRank1y,breakEvenProbability,time,averageVolatility,baseNextEarningsDate,timeCode,dividendExDate,historicVolatility30d,impliedVolatilityRank1y,baseTrendSpotterSignal,baseTrendSpotterStrength,symbolCode,symbolType",
        "meta": "expirations,field.shortName,field.type,field.description",
    }
    if expirationDate:
        params["expirationDate"] = expirationDate
    if expirationType:
        params["expirationType"] = expirationType

    query = urlencode(params)
    url = base_url + "?" + query
    return url


def bull_put_spreads(
    abs_deltaLeg1_low: str = "",
    abs_deltaLeg1_high: int | float = 0.6,
    abs_deltaLeg2_low: int | float = 0,
    abs_deltaLeg2_high: int | float = 0.3,
    riskRewardRatio_low: int | float = 2,
    riskRewardRatio_high: int | float = 5,
    baseSymbol: str = "AAPL",
    orderBy: str = "strikeLeg1",
    orderDir: str = "asc",
    expirationDate=None,
    expirationType=None,
    raw: int = 1,
) -> str:
    """URL builder for bull_put_spreads"""
    base_url = (
        "https://www.barchart.com/proxies/core-api/v1/options/bull-puts-spread"
    )
    params = {
        f"between(abs(deltaLeg1),{abs_deltaLeg1_low},{abs_deltaLeg1_high})": "",
        f"between(abs(deltaLeg2),{abs_deltaLeg2_low},{abs_deltaLeg2_high})": "",
        f"between(riskRewardRatio,{riskRewardRatio_low},{riskRewardRatio_high})": "",
        "baseSymbol": baseSymbol,
        "orderBy": orderBy,
        "orderDir": orderDir,
        "raw": raw,
        "fields": "baseSymbol,underlyingLastPrice,expirationDate,daysToExpiration,strikeLeg1,bidPriceLeg1,strikeLeg2,askPriceLeg2,breakEven,breakEvenPercent,maxProfit,maxLoss,maxProfitPercent,riskRewardRatio,impliedVolatilityRank1y,lossProbability,time,averageVolatility,baseNextEarningsDate,timeCode,dividendExDate,historicVolatility30d,impliedVolatilityRank1y,baseTrendSpotterSignal,baseTrendSpotterStrength,symbolCode,symbolType",
        "meta": "expirations,field.shortName,field.type,field.description",
    }
    if expirationDate:
        params["expirationDate"] = expirationDate
    if expirationType:
        params["expirationType"] = expirationType

    query = urlencode(params)
    url = base_url + "?" + query
    return url
