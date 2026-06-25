import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(os.environ.get("DB_PATH", "finance_trading_cockpit.sqlite3"))


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                name TEXT,
                sector TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.commit()


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def list_tickers() -> list[dict]:
    with connect() as db:
        rows = db.execute("SELECT id, symbol, name, sector FROM tickers ORDER BY symbol").fetchall()
    return [dict(row) for row in rows]


def add_ticker(symbol: str, name: str | None = None, sector: str | None = None) -> dict:
    clean_symbol = symbol.strip().upper()
    with connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO tickers (symbol, name, sector) VALUES (?, ?, ?)",
            (clean_symbol, name, sector),
        )
        db.commit()
        row = db.execute(
            "SELECT id, symbol, name, sector FROM tickers WHERE symbol = ?",
            (clean_symbol,),
        ).fetchone()
    return dict(row)


def delete_ticker(symbol: str) -> None:
    with connect() as db:
        db.execute("DELETE FROM tickers WHERE symbol = ?", (symbol.strip().upper(),))
        db.commit()

