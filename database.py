"""
Lokale SQLite-Datenbank für Wirtschaftsparameter und Aktienkurse.

Tabellen:
  stock_prices    – OHLCV-Tagesdaten der 7 Zielaktien
  economic_data   – Tages-/Monatswerte der 30 Makroparameter

Inkrementelles Update: Pro Ticker wird nur der Zeitraum ab dem letzten
gespeicherten Datum neu abgerufen.
"""

import sqlite3
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import date, timedelta
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from data_fetcher import ECONOMIC_PARAMS, TARGET_STOCKS, fetch_fred_series, _load_fred_key

DB_PATH = Path(__file__).parent / "wirtschaftstool.db"
HISTORY_START = "2004-01-01"   # 20 Jahre

console = Console()


# ─── Schema ─────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Erstellt Tabellen falls nicht vorhanden."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                symbol  TEXT    NOT NULL,
                date    DATE    NOT NULL,
                open    REAL,
                high    REAL,
                low     REAL,
                close   REAL,
                volume  INTEGER,
                PRIMARY KEY (symbol, date)
            );

            CREATE TABLE IF NOT EXISTS economic_data (
                parameter  TEXT  NOT NULL,
                ticker     TEXT  NOT NULL,
                date       DATE  NOT NULL,
                value      REAL,
                PRIMARY KEY (ticker, date)
            );

            CREATE INDEX IF NOT EXISTS idx_stock_symbol_date
                ON stock_prices (symbol, date);
            CREATE INDEX IF NOT EXISTS idx_eco_ticker_date
                ON economic_data (ticker, date);
        """)


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────────

def _last_date_stock(symbol: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM stock_prices WHERE symbol = ?", (symbol,)
        ).fetchone()
    return row[0] if row and row[0] else None


def _last_date_eco(ticker: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM economic_data WHERE ticker = ?", (ticker,)
        ).fetchone()
    return row[0] if row and row[0] else None


def _next_day(date_str: str) -> str:
    """Gibt das Folgedatum zurück (um Duplikate zu vermeiden)."""
    return str(date.fromisoformat(date_str) + timedelta(days=1))


# ─── Aktien laden ────────────────────────────────────────────────────────────────

def update_stock(symbol: str, yf_ticker: str) -> int:
    """
    Lädt fehlende Kursdaten für eine Aktie nach und speichert sie in der DB.
    Gibt die Anzahl neu eingefügter Zeilen zurück.
    """
    last = _last_date_stock(symbol)
    start = _next_day(last) if last else HISTORY_START

    if start > str(date.today()):
        return 0  # bereits aktuell

    try:
        t = yf.Ticker(yf_ticker)
        hist = t.history(start=start, end=str(date.today() + timedelta(days=1)), auto_adjust=True)
    except Exception as e:
        console.print(f"[yellow]  Fehler beim Abrufen von {symbol}: {e}[/yellow]")
        return 0

    if hist.empty:
        return 0

    rows = []
    for dt, row in hist.iterrows():
        rows.append((
            symbol,
            str(dt.date()),
            float(row["Open"])   if pd.notna(row["Open"])   else None,
            float(row["High"])   if pd.notna(row["High"])   else None,
            float(row["Low"])    if pd.notna(row["Low"])    else None,
            float(row["Close"])  if pd.notna(row["Close"])  else None,
            int(row["Volume"])   if pd.notna(row["Volume"]) else None,
        ))

    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO stock_prices (symbol,date,open,high,low,close,volume) "
            "VALUES (?,?,?,?,?,?,?)",
            rows,
        )

    return len(rows)


def update_all_stocks() -> dict:
    """Aktualisiert alle 7 Zielaktien. Gibt Symbol→Anzahl-neue-Zeilen zurück."""
    init_db()
    results = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Aktienkurse aktualisieren…", total=len(TARGET_STOCKS))
        for symbol, meta in TARGET_STOCKS.items():
            progress.update(task, description=f"Aktie: {symbol:<6}")
            n = update_stock(symbol, meta["ticker"])
            results[symbol] = n
            progress.advance(task)
    return results


# ─── Wirtschaftsparameter laden ──────────────────────────────────────────────────

def update_eco_yfinance(name: str, ticker: str) -> int:
    """Lädt yfinance-Zeitreihe nach (täglich)."""
    last = _last_date_eco(ticker)
    start = _next_day(last) if last else HISTORY_START

    if start > str(date.today()):
        return 0

    try:
        t = yf.Ticker(ticker)
        hist = t.history(start=start, end=str(date.today() + timedelta(days=1)), auto_adjust=True)
    except Exception:
        return 0

    if hist.empty:
        return 0

    rows = []
    for dt, row in hist.iterrows():
        val = row.get("Close")
        if pd.notna(val):
            rows.append((name, ticker, str(dt.date()), float(val)))

    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO economic_data (parameter,ticker,date,value) VALUES (?,?,?,?)",
            rows,
        )

    return len(rows)


def update_eco_fred(name: str, series_id: str) -> int:
    """Lädt FRED-Zeitreihe nach (monatlich)."""
    api_key = _load_fred_key()
    if not api_key:
        return 0

    last = _last_date_eco(series_id)

    try:
        from fredapi import Fred
        fred = Fred(api_key=api_key)
        obs_start = _next_day(last) if last else HISTORY_START
        series = fred.get_series(series_id, observation_start=obs_start)
        series = series.dropna()
    except Exception:
        return 0

    if series.empty:
        return 0

    rows = [(name, series_id, str(dt.date()), float(val)) for dt, val in series.items()]

    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO economic_data (parameter,ticker,date,value) VALUES (?,?,?,?)",
            rows,
        )

    return len(rows)


def update_all_economic() -> dict:
    """Aktualisiert alle 30 Wirtschaftsparameter. Gibt ticker→Anzahl-neue-Zeilen zurück."""
    init_db()
    results = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Wirtschaftsdaten aktualisieren…", total=len(ECONOMIC_PARAMS))
        for name, meta in ECONOMIC_PARAMS.items():
            progress.update(task, description=f"Makro: {name[:28]:<28}")
            if meta["source"] == "yfinance":
                n = update_eco_yfinance(name, meta["ticker"])
            else:
                n = update_eco_fred(name, meta["ticker"])
            results[meta["ticker"]] = n
            progress.advance(task)
    return results


# ─── Lesezugriff ────────────────────────────────────────────────────────────────

def load_stock_prices(symbol: str) -> pd.DataFrame:
    """Gibt alle Kursdaten einer Aktie als DataFrame zurück."""
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT date, open, high, low, close, volume FROM stock_prices "
            "WHERE symbol = ? ORDER BY date",
            conn, params=(symbol,), parse_dates=["date"],
        )
    df.set_index("date", inplace=True)
    df.columns = [c.capitalize() for c in df.columns]
    return df


def load_economic_series(ticker: str) -> pd.Series:
    """Gibt eine Wirtschaftszeitreihe als Series zurück."""
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT date, value FROM economic_data WHERE ticker = ? ORDER BY date",
            conn, params=(ticker,), parse_dates=["date"],
        )
    if df.empty:
        return pd.Series(dtype=float)
    df.set_index("date", inplace=True)
    return df["value"].rename(ticker)


def db_summary() -> pd.DataFrame:
    """Zeigt Anzahl Datenpunkte und Datumsbereich je Ticker."""
    with get_connection() as conn:
        stocks = pd.read_sql_query(
            "SELECT symbol as ticker, COUNT(*) as rows, MIN(date) as von, MAX(date) as bis "
            "FROM stock_prices GROUP BY symbol ORDER BY symbol",
            conn,
        )
        eco = pd.read_sql_query(
            "SELECT ticker, COUNT(*) as rows, MIN(date) as von, MAX(date) as bis "
            "FROM economic_data GROUP BY ticker ORDER BY ticker",
            conn,
        )
    stocks["typ"] = "Aktie"
    eco["typ"] = "Makro"
    return pd.concat([stocks, eco], ignore_index=True)
