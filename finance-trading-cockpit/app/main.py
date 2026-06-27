from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import HistoryPoint, Quote, Signal, SymbolSearchResult, Ticker, TickerCreate, TickerInsight
from app.services.market_data import get_history, get_history_range, get_quote, normalize_range, search_symbols
from app.services.news import get_news
from app.services.signals import build_signal
from app.services.storage import add_ticker, delete_ticker, init_db, list_tickers


app = FastAPI(title="Finance Trading Cockpit", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.get("/")
async def index():
    return FileResponse("app/static/index.html")


@app.get("/api/tickers", response_model=list[Ticker])
async def api_list_tickers():
    return list_tickers()


@app.post("/api/tickers", response_model=Ticker)
async def api_add_ticker(payload: TickerCreate):
    return add_ticker(payload.symbol, payload.name, payload.sector, payload.notes)


@app.delete("/api/tickers/{symbol}")
async def api_delete_ticker(symbol: str):
    delete_ticker(symbol)
    return {"ok": True}


@app.get("/api/news")
async def api_news(q: str | None = Query(default=None)):
    symbols = [ticker["symbol"] for ticker in list_tickers()]
    return await get_news(symbols, q)


@app.get("/api/search", response_model=list[SymbolSearchResult])
async def api_search(q: str = Query(min_length=2), limit: int = Query(default=8, ge=1, le=20)):
    return await search_symbols(q, limit)


@app.get("/api/signals", response_model=list[Signal])
async def api_signals():
    tickers = list_tickers()
    if not tickers:
        return []

    symbols = [ticker["symbol"] for ticker in tickers]
    all_news = await get_news(symbols)
    signals = []
    for ticker in tickers:
        symbol = ticker["symbol"]
        try:
            quote = await get_quote(symbol)
            related_news = [item for item in all_news if symbol in item.symbols] or all_news
            signals.append(build_signal(symbol, quote, related_news))
        except Exception as exc:
            signals.append(_unavailable_signal(symbol, str(exc)))
    return signals


@app.get("/api/overview", response_model=list[TickerInsight])
async def api_overview(
    range: str = Query(default="1M"),
    days: int | None = Query(default=None, ge=1, le=365),
):
    tickers = list_tickers()
    if not tickers:
        return []

    chart_range = normalize_range(range if days is None else f"{days}D")
    symbols = [ticker["symbol"] for ticker in tickers]
    all_news = await get_news(symbols)
    overview = []
    for ticker in tickers:
        symbol = ticker["symbol"]
        try:
            quote = await get_quote(symbol)
            related_news = [item for item in all_news if symbol in item.symbols] or all_news
            signal = build_signal(symbol, quote, related_news)
            history = await get_history(symbol, days) if days is not None else await get_history_range(symbol, chart_range)
            range_change, range_change_percent = _range_performance(history)
            range_reason = _range_reason(chart_range, range_change, range_change_percent, quote.currency)
            if range_reason:
                signal.reasons.insert(0, range_reason)
            first_close = history[0].close if history else None
            last_close = history[-1].close if history else None
            calculation_note = _calculation_note(chart_range, first_close, last_close, quote.currency)
        except Exception as exc:
            signal = _unavailable_signal(symbol, str(exc))
            history = []
            range_change = None
            range_change_percent = None
            first_close = None
            last_close = None
            calculation_note = None
        overview.append(
            {
                "ticker": ticker,
                "signal": signal,
                "history": history,
                "chart_source": signal.quote.source,
                "chart_range": chart_range,
                "chart_as_of": signal.quote.as_of,
                "chart_source_url": signal.quote.source_url,
                "range_change": range_change,
                "range_change_percent": range_change_percent,
                "history_points": len(history),
                "first_close": first_close,
                "last_close": last_close,
                "calculation_note": calculation_note,
            }
        )
    return overview


@app.get("/api/history/{symbol}", response_model=list[HistoryPoint])
async def api_history(
    symbol: str,
    range: str = Query(default="1M"),
    days: int | None = Query(default=None, ge=1, le=365),
):
    if days is not None:
        return await get_history(symbol.upper(), days)
    return await get_history_range(symbol.upper(), normalize_range(range))


@app.get("/api/signals/{symbol}", response_model=Signal)
async def api_signal(symbol: str):
    tickers = {ticker["symbol"] for ticker in list_tickers()}
    clean_symbol = symbol.upper()
    if clean_symbol not in tickers:
        raise HTTPException(status_code=404, detail="Ticker not in watchlist")

    quote = await get_quote(clean_symbol)
    news = await get_news([clean_symbol])
    return build_signal(clean_symbol, quote, news)


def _unavailable_signal(symbol: str, reason: str) -> Signal:
    return Signal(
        symbol=symbol.upper(),
        stance="Non disponibile",
        score=0,
        reasons=[f"Dati mercato non disponibili: {reason}"],
        quote=Quote(symbol=symbol.upper(), price=0, change_percent=0, volume=0, source="unavailable"),
        news=[],
    )


def _range_performance(history: list[HistoryPoint]) -> tuple[float | None, float | None]:
    if len(history) < 2:
        return None, None
    first = history[0].close
    last = history[-1].close
    if first == 0:
        return None, None
    change = round(last - first, 2)
    change_percent = round((change / first) * 100, 2)
    return change, change_percent


def _range_reason(
    range_key: str,
    change: float | None,
    change_percent: float | None,
    currency: str,
) -> str | None:
    if change is None or change_percent is None:
        return None
    labels = {
        "1D": "oggi",
        "1W": "nell'ultima settimana",
        "1M": "nell'ultimo mese",
        "1Y": "nell'ultimo anno",
        "ALL": "sul periodo totale disponibile",
    }
    direction = "positivo" if change_percent >= 0 else "negativo"
    return f"Trend {direction} {labels.get(range_key, range_key)}: {currency} {change:+.2f} ({change_percent:+.2f}%)"


def _calculation_note(
    range_key: str,
    first_close: float | None,
    last_close: float | None,
    currency: str,
) -> str | None:
    if first_close is None or last_close is None:
        return None
    return (
        f"{range_key}: ((ultimo {currency} {last_close:.2f} - "
        f"primo {currency} {first_close:.2f}) / primo) * 100"
    )
