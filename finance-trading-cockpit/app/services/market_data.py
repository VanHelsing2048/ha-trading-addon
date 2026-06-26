import hashlib
import os
import random
import time
from datetime import UTC, date, datetime, timedelta

import httpx

from app.models import HistoryPoint, Quote, SymbolSearchResult


YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
HTTP_TIMEOUT = 8.0


def _stable_rng(symbol: str) -> random.Random:
    seed = int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(seed)


async def get_quote(symbol: str) -> Quote:
    if os.environ.get("DATA_MODE", "live") == "demo":
        return _demo_quote(symbol)

    return await _get_yahoo_quote(symbol)


async def get_history(symbol: str, days: int = 30) -> list[HistoryPoint]:
    if os.environ.get("DATA_MODE", "live") == "demo":
        return await _demo_history(symbol, days)

    return await _get_yahoo_history(symbol, days)


async def get_history_range(symbol: str, range_key: str = "1M") -> list[HistoryPoint]:
    clean_range = normalize_range(range_key)
    if os.environ.get("DATA_MODE", "live") == "demo":
        demo_days = {"1D": 1, "1W": 7, "1M": 30, "1Y": 365, "ALL": 365}.get(clean_range, 30)
        return await _demo_history(symbol, demo_days)

    return await _get_yahoo_history_range(symbol, clean_range)


def normalize_range(range_key: str) -> str:
    clean = range_key.strip().upper()
    aliases = {
        "TODAY": "1D",
        "DAY": "1D",
        "1D": "1D",
        "7D": "1W",
        "1W": "1W",
        "30D": "1M",
        "1M": "1M",
        "365D": "1Y",
        "1Y": "1Y",
        "MAX": "ALL",
        "TOTAL": "ALL",
        "ALL": "ALL",
    }
    return aliases.get(clean, "1M")


async def search_symbols(query: str, limit: int = 8) -> list[SymbolSearchResult]:
    clean_query = query.strip()
    if len(clean_query) < 2:
        return []

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        response = await client.get(
            YAHOO_SEARCH_URL,
            params={"q": clean_query, "quotesCount": limit, "newsCount": 0},
            headers={"User-Agent": "ha-trading-addon/0.2"},
        )
        response.raise_for_status()
        payload = response.json()

    results = []
    for item in payload.get("quotes", [])[:limit]:
        symbol = item.get("symbol")
        if not symbol:
            continue
        results.append(
            SymbolSearchResult(
                symbol=symbol,
                name=item.get("shortname") or item.get("longname"),
                exchange=item.get("exchange"),
                quote_type=item.get("quoteType"),
                sector=item.get("sector"),
            )
        )
    return results


def _demo_quote(symbol: str) -> Quote:
    rng = _stable_rng(symbol.upper())
    base_price = rng.uniform(20, 700)
    change = rng.uniform(-4.5, 4.5)
    volume = rng.randint(500_000, 95_000_000)

    return Quote(
        symbol=symbol.upper(),
        price=round(base_price * (1 + change / 100), 2),
        change_percent=round(change, 2),
        volume=volume,
        source="demo",
    )


async def _demo_history(symbol: str, days: int = 30) -> list[HistoryPoint]:
    clean_symbol = symbol.upper()
    rng = _stable_rng(f"{clean_symbol}:{days}")
    quote = await get_quote(clean_symbol)
    days = max(7, min(days, 365))
    today = date.today()
    price = quote.price / rng.uniform(0.88, 1.16)
    points: list[HistoryPoint] = []

    for index in range(days):
        remaining = days - index
        drift = (quote.price - price) / max(remaining, 1)
        price += drift + rng.uniform(-1.8, 1.8)
        price = max(0.1, price)
        points.append(
            HistoryPoint(
                date=(today - timedelta(days=days - index - 1)).isoformat(),
                close=round(price, 2),
            )
        )

    points[-1] = HistoryPoint(date=today.isoformat(), close=quote.price)
    return points


async def _get_yahoo_quote(symbol: str) -> Quote:
    payload = await _get_yahoo_chart(symbol, "5d", "1d")
    result = _first_chart_result(payload)
    meta = result.get("meta", {})
    price = meta.get("regularMarketPrice")
    previous_close = meta.get("previousClose") or meta.get("chartPreviousClose")
    volume = meta.get("regularMarketVolume") or 0

    if price is None:
        closes = _valid_closes(result)
        if not closes:
            raise ValueError(f"No live quote available for {symbol}")
        price = closes[-1]

    if previous_close:
        change_percent = ((float(price) - float(previous_close)) / float(previous_close)) * 100
    else:
        closes = _valid_closes(result)
        base = closes[-2] if len(closes) > 1 else price
        change_percent = ((float(price) - float(base)) / float(base)) * 100 if base else 0

    return Quote(
        symbol=symbol.upper(),
        price=round(float(price), 2),
        change_percent=round(change_percent, 2),
        volume=int(volume or 0),
        source="yahoo",
    )


async def _get_yahoo_history(symbol: str, days: int = 30) -> list[HistoryPoint]:
    days = max(7, min(days, 365))
    period2 = int(time.time())
    period1 = period2 - (days + 10) * 24 * 60 * 60
    payload = await _get_yahoo_chart(
        symbol,
        None,
        "1d",
        extra_params={"period1": period1, "period2": period2},
    )
    result = _first_chart_result(payload)
    timestamps = result.get("timestamp", [])
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])

    points = []
    for timestamp, close in zip(timestamps, closes, strict=False):
        if close is None:
            continue
        day = datetime.fromtimestamp(timestamp, tz=UTC).date().isoformat()
        points.append(HistoryPoint(date=day, close=round(float(close), 2)))

    if not points:
        raise ValueError(f"No historical prices available for {symbol}")
    return points[-days:]


async def _get_yahoo_history_range(symbol: str, range_key: str) -> list[HistoryPoint]:
    yahoo_range, interval = {
        "1D": ("1d", "5m"),
        "1W": ("5d", "15m"),
        "1M": ("1mo", "1d"),
        "1Y": ("1y", "1d"),
        "ALL": ("max", "1mo"),
    }[range_key]
    payload = await _get_yahoo_chart(symbol, yahoo_range, interval)
    result = _first_chart_result(payload)
    timestamps = result.get("timestamp", [])
    quote = result.get("indicators", {}).get("quote", [{}])[0]
    closes = quote.get("close", [])

    points = []
    for timestamp, close in zip(timestamps, closes, strict=False):
        if close is None:
            continue
        moment = datetime.fromtimestamp(timestamp, tz=UTC)
        label = moment.isoformat() if range_key in {"1D", "1W"} else moment.date().isoformat()
        points.append(HistoryPoint(date=label, close=round(float(close), 2)))

    if not points:
        raise ValueError(f"No historical prices available for {symbol}")
    return points


async def _get_yahoo_chart(
    symbol: str,
    range_value: str | None,
    interval: str,
    extra_params: dict | None = None,
) -> dict:
    params = {"interval": interval}
    if range_value:
        params["range"] = range_value
    if extra_params:
        params.update(extra_params)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        response = await client.get(
            YAHOO_CHART_URL.format(symbol=symbol.upper()),
            params=params,
            headers={"User-Agent": "ha-trading-addon/0.2"},
        )
        response.raise_for_status()
        return response.json()


def _first_chart_result(payload: dict) -> dict:
    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        raise ValueError(error.get("description") or "Yahoo chart error")
    results = chart.get("result") or []
    if not results:
        raise ValueError("Yahoo returned no chart result")
    return results[0]


def _valid_closes(result: dict) -> list[float]:
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    return [float(close) for close in closes if close is not None]
