import csv
import os
from datetime import UTC, datetime
from io import StringIO

import httpx

from app.models import CorporateEvents


ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_SOURCE_URL = "https://www.alphavantage.co/"
HTTP_TIMEOUT = 8.0


async def get_corporate_events(symbol: str) -> CorporateEvents:
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    clean_symbol = symbol.upper()
    if not api_key:
        return CorporateEvents(
            symbol=clean_symbol,
            source="unavailable",
            source_url=ALPHA_VANTAGE_SOURCE_URL,
            notes=["Alpha Vantage API key non configurata"],
        )

    overview = {}
    earnings_date = None
    notes = []
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            overview = await _get_overview(client, clean_symbol, api_key)
        except Exception as exc:
            notes.append(f"Overview non disponibile: {exc}")
        try:
            earnings_date = await _get_next_earnings_date(client, clean_symbol, api_key)
        except Exception as exc:
            notes.append(f"Calendario utili non disponibile: {exc}")

    return CorporateEvents(
        symbol=clean_symbol,
        next_earnings_date=earnings_date,
        dividend_date=_empty_to_none(overview.get("DividendDate")),
        ex_dividend_date=_empty_to_none(overview.get("ExDividendDate")),
        source="alpha_vantage",
        as_of=datetime.now(UTC).isoformat(),
        source_url=ALPHA_VANTAGE_SOURCE_URL,
        notes=notes,
    )


async def _get_overview(client: httpx.AsyncClient, symbol: str, api_key: str) -> dict:
    response = await client.get(
        ALPHA_VANTAGE_URL,
        params={"function": "OVERVIEW", "symbol": symbol, "apikey": api_key},
        headers={"User-Agent": "ha-trading-addon/0.5"},
    )
    response.raise_for_status()
    payload = response.json()
    _raise_alpha_message(payload)
    return payload


async def _get_next_earnings_date(client: httpx.AsyncClient, symbol: str, api_key: str) -> str | None:
    response = await client.get(
        ALPHA_VANTAGE_URL,
        params={
            "function": "EARNINGS_CALENDAR",
            "symbol": symbol,
            "horizon": "3month",
            "apikey": api_key,
        },
        headers={"User-Agent": "ha-trading-addon/0.5"},
    )
    response.raise_for_status()
    text = response.text.strip()
    if not text or text.startswith("{"):
        return None

    rows = csv.DictReader(StringIO(text))
    today = datetime.now(UTC).date()
    upcoming = []
    for row in rows:
        report_date = _empty_to_none(row.get("reportDate"))
        if not report_date:
            continue
        try:
            parsed = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if parsed >= today:
            upcoming.append(report_date)
    return sorted(upcoming)[0] if upcoming else None


def _raise_alpha_message(payload: dict) -> None:
    message = payload.get("Error Message") or payload.get("Note") or payload.get("Information")
    if message:
        raise ValueError(str(message))


def _empty_to_none(value: str | None) -> str | None:
    if not value or value in {"None", "0000-00-00"}:
        return None
    return value
