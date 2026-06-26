from pydantic import BaseModel, Field


class TickerCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=120)
    sector: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=500)


class Ticker(TickerCreate):
    id: int
    symbol: str


class Quote(BaseModel):
    symbol: str
    price: float
    currency: str = "USD"
    price_eur: float | None = None
    price_usd: float | None = None
    eur_usd_rate: float | None = None
    change_percent: float
    volume: int
    source: str
    as_of: str | None = None
    source_url: str | None = None


class SymbolSearchResult(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    quote_type: str | None = None
    sector: str | None = None


class HistoryPoint(BaseModel):
    date: str
    close: float
    close_eur: float | None = None
    close_usd: float | None = None


class TickerInsight(BaseModel):
    ticker: Ticker
    signal: "Signal"
    history: list[HistoryPoint]
    chart_source: str = "unknown"
    chart_range: str = "1M"
    chart_as_of: str | None = None
    chart_source_url: str | None = None
    range_change: float | None = None
    range_change_percent: float | None = None


class NewsItem(BaseModel):
    title: str
    link: str
    source: str
    published: str | None = None
    summary: str | None = None
    symbols: list[str] = []


class Signal(BaseModel):
    symbol: str
    stance: str
    score: int
    reasons: list[str]
    quote: Quote
    news: list[NewsItem]


TickerInsight.model_rebuild()
