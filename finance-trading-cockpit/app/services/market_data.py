import hashlib
import random

from app.models import Quote


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

