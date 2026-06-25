from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import HistoryPoint, Quote, Signal, SymbolSearchResult, Ticker, TickerCreate, TickerInsight
from app.services.market_data import get_history, get_quote, search_symbols
from app.services.news import get_news
from app.services.signals import build_signal
from app.services.storage import add_ticker, delete_ticker, init_db, list_tickers


app = FastAPI(title="Finance Trading Cockpit", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def startup() -> None:
    init_db()
    if not list_tickers():
        for symbol, name, sector in [
            ("AAPL", "Apple", "Technology"),
            ("NVDA", "Nvidia", "Semiconductors"),
            ("BTC-USD", "Bitcoin", "Crypto"),
        ]:
            add_ticker(symbol, name, sector)


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
async def api_overview(days: int = Query(default=30, ge=7, le=365)):
    tickers = list_tickers()
    if not tickers:
        return []

    symbols = [ticker["symbol"] for ticker in tickers]
    all_news = await get_news(symbols)
    overview = []
    for ticker in tickers:
        symbol = ticker["symbol"]
        try:
            quote = await get_quote(symbol)
            related_news = [item for item in all_news if symbol in item.symbols] or all_news
            signal = build_signal(symbol, quote, related_news)
            history = await get_history(symbol, days)
        except Exception as exc:
            signal = _unavailable_signal(symbol, str(exc))
            history = []
        overview.append({"ticker": ticker, "signal": signal, "history": history})
    return overview


@app.get("/api/history/{symbol}", response_model=list[HistoryPoint])
async def api_history(symbol: str, days: int = Query(default=30, ge=7, le=365)):
    return await get_history(symbol.upper(), days)


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
