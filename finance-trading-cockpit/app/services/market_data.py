import hashlib
import random
from datetime import date, timedelta

from app.models import HistoryPoint, Quote


def _stable_rng(symbol: str) -> random.Random:
    seed = int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(seed)


async def get_quote(symbol: str) -> Quote:
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


async def get_history(symbol: str, days: int = 30) -> list[HistoryPoint]:
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
