from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import Signal, Ticker, TickerCreate
from app.services.market_data import get_quote
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
    return add_ticker(payload.symbol, payload.name, payload.sector)


@app.delete("/api/tickers/{symbol}")
async def api_delete_ticker(symbol: str):
    delete_ticker(symbol)
    return {"ok": True}


@app.get("/api/news")
async def api_news(q: str | None = Query(default=None)):
    symbols = [ticker["symbol"] for ticker in list_tickers()]
    return await get_news(symbols, q)


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
        quote = await get_quote(symbol)
        related_news = [item for item in all_news if symbol in item.symbols] or all_news
        signals.append(build_signal(symbol, quote, related_news))
    return signals


@app.get("/api/signals/{symbol}", response_model=Signal)
async def api_signal(symbol: str):
    tickers = {ticker["symbol"] for ticker in list_tickers()}
    clean_symbol = symbol.upper()
    if clean_symbol not in tickers:
        raise HTTPException(status_code=404, detail="Ticker not in watchlist")

    quote = await get_quote(clean_symbol)
    news = await get_news([clean_symbol])
    return build_signal(clean_symbol, quote, news)

