"""
Modul zum Abrufen von Wirtschaftsdaten via yfinance und FRED API.
"""

import os
import re
import yfinance as yf
import pandas as pd
from pathlib import Path
from typing import Optional

# FRED-API-Key: wird aus fred_API_Key.txt im Projektverzeichnis gelesen
def _load_fred_key() -> str:
    key_file = Path(__file__).parent / "fred_API_Key.txt"
    if key_file.exists():
        content = key_file.read_text()
        # Format: "API Key: <key>" oder direkt der Key
        m = re.search(r"API Key:\s*([a-f0-9]{32})", content, re.IGNORECASE)
        if m:
            return m.group(1)
        # Fallback: erste 32-stellige Hex-Sequenz
        m = re.search(r"[a-f0-9]{32}", content, re.IGNORECASE)
        if m:
            return m.group(0)
    return os.environ.get("FRED_API_KEY", "")

FRED_API_KEY = _load_fred_key()

# ─── Definitionen ───────────────────────────────────────────────────────────────

ECONOMIC_PARAMS = {
    # Rohstoffe
    "WTI Rohöl":        {"ticker": "CL=F",              "source": "yfinance", "region": "Global"},
    "Brent Rohöl":      {"ticker": "BZ=F",              "source": "yfinance", "region": "Global"},
    "Gold":             {"ticker": "GC=F",              "source": "yfinance", "region": "Global"},
    "Silber":           {"ticker": "SI=F",              "source": "yfinance", "region": "Global"},
    "Kupfer":           {"ticker": "HG=F",              "source": "yfinance", "region": "Global"},
    "Erdgas":           {"ticker": "NG=F",              "source": "yfinance", "region": "Global"},
    "Platin":           {"ticker": "PL=F",              "source": "yfinance", "region": "Global"},
    "Palladium":        {"ticker": "PA=F",              "source": "yfinance", "region": "Global"},
    # Indizes – EUR-Raum
    "DAX":              {"ticker": "^GDAXI",            "source": "yfinance", "region": "EUR"},
    "Euro Stoxx 50":    {"ticker": "^STOXX50E",         "source": "yfinance", "region": "EUR"},
    "CAC 40":           {"ticker": "^FCHI",             "source": "yfinance", "region": "EUR"},
    # Indizes – USD-Raum
    "S&P 500":          {"ticker": "^GSPC",             "source": "yfinance", "region": "USD"},
    "Dow Jones":        {"ticker": "^DJI",              "source": "yfinance", "region": "USD"},
    "NASDAQ 100":       {"ticker": "^NDX",              "source": "yfinance", "region": "USD"},
    "FTSE 100":         {"ticker": "^FTSE",             "source": "yfinance", "region": "GBP"},
    # Volatilität
    "VIX":              {"ticker": "^VIX",              "source": "yfinance", "region": "USD"},
    "VSTOXX (V2TX)":    {"ticker": "^V2TX",              "source": "yfinance", "region": "EUR"},
    # Wechselkurse
    "EUR/USD":          {"ticker": "EURUSD=X",          "source": "yfinance", "region": "EUR/USD"},
    "GBP/USD":          {"ticker": "GBPUSD=X",          "source": "yfinance", "region": "GBP/USD"},
    "USD/JPY":          {"ticker": "JPY=X",             "source": "yfinance", "region": "USD/JPY"},
    "USD/CHF":          {"ticker": "CHF=X",             "source": "yfinance", "region": "USD/CHF"},
    "USD/CNY":          {"ticker": "CNY=X",             "source": "yfinance", "region": "USD/CNY"},
    "USD-Index (DXY)":  {"ticker": "DX=F",               "source": "yfinance", "region": "USD"},
    # Anleiherenditen
    "US 10J Rendite":   {"ticker": "^TNX",              "source": "yfinance", "region": "USD"},
    "US 30J Rendite":   {"ticker": "^TYX",              "source": "yfinance", "region": "USD"},
    "US 5J Rendite":    {"ticker": "^FVX",              "source": "yfinance", "region": "USD"},
    # ETF
    "MSCI World ETF":   {"ticker": "URTH",              "source": "yfinance", "region": "Global"},
    # Krypto
    "Bitcoin":          {"ticker": "BTC-USD",           "source": "yfinance", "region": "Global"},
    # Inflation (FRED)
    "US Inflation CPI": {"ticker": "CPIAUCSL",         "source": "fred",     "region": "USD"},
    "EU Inflation HICP":{"ticker": "CP0000EZ19M086NEST","source": "fred",    "region": "EUR"},
}

# Zielaktien mit korrekten Tickern (XETRA / NASDAQ)
TARGET_STOCKS = {
    "DBK":  {"ticker": "DBK.DE",  "name": "Deutsche Bank",    "exchange": "XETRA"},
    "SIE":  {"ticker": "SIE.DE",  "name": "Siemens",          "exchange": "XETRA"},
    "ALV":  {"ticker": "ALV.DE",  "name": "Allianz",          "exchange": "XETRA"},
    "DTE":  {"ticker": "DTE.DE",  "name": "Deutsche Telekom", "exchange": "XETRA"},
    "RGLD": {"ticker": "RGLD",    "name": "Royal Gold",       "exchange": "NASDAQ"},
    "AMZN": {"ticker": "AMZN",    "name": "Amazon",           "exchange": "NASDAQ"},
    "BNP":  {"ticker": "BNP.PA",  "name": "BNP Paribas",      "exchange": "Euronext"},
}


# ─── Abruf-Funktionen ───────────────────────────────────────────────────────────

def fetch_current_price(ticker: str) -> Optional[float]:
    """Aktuellen Kurs eines Tickers abrufen."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = getattr(info, "last_price", None)
        if price is None:
            hist = t.history(period="2d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]
        return price
    except Exception:
        return None


def fetch_history(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """Historische OHLCV-Daten abrufen."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if hist.empty:
            return None
        return hist
    except Exception:
        return None


def fetch_fred_series(series_id: str) -> Optional[float]:
    """Letzten Wert einer FRED-Zeitreihe abrufen (benötigt API-Key)."""
    if not FRED_API_KEY:
        return None
    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_API_KEY)
        series = fred.get_series(series_id)
        return float(series.dropna().iloc[-1])
    except Exception:
        return None


def fetch_all_economic_params() -> pd.DataFrame:
    """Alle 30 Wirtschaftsparameter abrufen und als DataFrame zurückgeben."""
    rows = []
    for name, meta in ECONOMIC_PARAMS.items():
        if meta["source"] == "yfinance":
            price = fetch_current_price(meta["ticker"])
        else:
            price = fetch_fred_series(meta["ticker"])

        rows.append({
            "Parameter":  name,
            "Ticker":     meta["ticker"],
            "Quelle":     meta["source"],
            "Raum":       meta["region"],
            "Aktuell":    round(price, 4) if price is not None else "N/A",
        })
    return pd.DataFrame(rows)


def fetch_stock_history(symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """Historische Kursdaten einer Zielaktie abrufen."""
    info = TARGET_STOCKS.get(symbol)
    if info is None:
        return None
    return fetch_history(info["ticker"], period=period)
