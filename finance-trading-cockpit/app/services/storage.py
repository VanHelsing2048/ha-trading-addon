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
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row["name"] for row in db.execute("PRAGMA table_info(tickers)").fetchall()}
        if "notes" not in columns:
            db.execute("ALTER TABLE tickers ADD COLUMN notes TEXT")
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
        rows = db.execute("SELECT id, symbol, name, sector, notes FROM tickers ORDER BY symbol").fetchall()
    return [dict(row) for row in rows]


def add_ticker(
    symbol: str,
    name: str | None = None,
    sector: str | None = None,
    notes: str | None = None,
) -> dict:
    clean_symbol = symbol.strip().upper()
    with connect() as db:
        db.execute(
            """
            INSERT INTO tickers (symbol, name, sector, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
                sector = excluded.sector,
                notes = excluded.notes
            """,
            (clean_symbol, name, sector, notes),
        )
        db.commit()
        row = db.execute(
            "SELECT id, symbol, name, sector, notes FROM tickers WHERE symbol = ?",
            (clean_symbol,),
        ).fetchone()
    return dict(row)


def delete_ticker(symbol: str) -> None:
    with connect() as db:
        db.execute("DELETE FROM tickers WHERE symbol = ?", (symbol.strip().upper(),))
        db.commit()
