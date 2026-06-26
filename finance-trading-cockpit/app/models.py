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
    change_percent: float
    volume: int
    source: str


class SymbolSearchResult(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    quote_type: str | None = None
    sector: str | None = None


class HistoryPoint(BaseModel):
    date: str
    close: float


class TickerInsight(BaseModel):
    ticker: Ticker
    signal: "Signal"
    history: list[HistoryPoint]
    chart_source: str = "unknown"
    chart_range: str = "1M"


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
