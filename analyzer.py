"""
Technische Analyse: Berechnung von Indikatoren und Erzeugung von Kauf-/Verkaufsempfehlungen.

Indikatoren:
  - SMA 20 / 50 / 200 (Gleitende Durchschnitte)
  - RSI 14 (Relative Strength Index)
  - MACD (12/26/9)
  - Bollinger Bänder (20, ±2σ)
  - ATR 14 (Volatilität)

Scoring-System (jeder Indikator liefert +1 / 0 / -1):
  ≥ +3  → STRONG BUY
  +1/+2 → BUY
    0   → HOLD
  -1/-2 → SELL
  ≤ -3  → STRONG SELL
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnalysisResult:
    symbol:       str
    name:         str
    current_price: Optional[float]
    currency:     str
    score:        int
    recommendation: str
    signals:      dict = field(default_factory=dict)
    indicators:   dict = field(default_factory=dict)


# ─── Indikatoren ────────────────────────────────────────────────────────────────

def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series):
    ema12 = _ema(series, 12)
    ema26 = _ema(series, 26)
    macd_line = ema12 - ema26
    signal_line = _ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = _sma(series, window)
    std = series.rolling(window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ─── Analyse ────────────────────────────────────────────────────────────────────

def _score_to_recommendation(score: int) -> str:
    if score >= 3:
        return "STRONG BUY"
    elif score >= 1:
        return "BUY"
    elif score <= -3:
        return "STRONG SELL"
    elif score <= -1:
        return "SELL"
    else:
        return "HOLD"


def analyze(symbol: str, name: str, hist: pd.DataFrame, currency: str = "EUR") -> AnalysisResult:
    """
    Analysiert historische OHLCV-Daten und liefert eine Empfehlung.

    Parameters
    ----------
    symbol  : Kürzel (z.B. 'DBK')
    name    : Vollständiger Name
    hist    : DataFrame mit Spalten Open/High/Low/Close/Volume (yfinance-Format)
    currency: Währung der Kurse
    """
    close = hist["Close"].squeeze()
    high  = hist["High"].squeeze()
    low   = hist["Low"].squeeze()

    current_price = float(close.iloc[-1])

    # ── Indikatoren berechnen ──
    sma20  = _sma(close, 20).iloc[-1]
    sma50  = _sma(close, 50).iloc[-1]
    sma200 = _sma(close, 200).iloc[-1]
    rsi    = _rsi(close).iloc[-1]
    macd_line, signal_line, histogram = _macd(close)
    macd_val  = macd_line.iloc[-1]
    signal_val= signal_line.iloc[-1]
    hist_val  = histogram.iloc[-1]
    bb_upper, bb_mid, bb_lower = _bollinger(close)
    bb_up  = bb_upper.iloc[-1]
    bb_lo  = bb_lower.iloc[-1]
    atr    = _atr(high, low, close).iloc[-1]

    indicators = {
        "Kurs":        round(current_price, 2),
        "SMA20":       round(sma20,  2),
        "SMA50":       round(sma50,  2),
        "SMA200":      round(sma200, 2),
        "RSI(14)":     round(rsi,    1),
        "MACD":        round(macd_val, 4),
        "MACD Signal": round(signal_val, 4),
        "BB Oben":     round(bb_up, 2),
        "BB Unten":    round(bb_lo, 2),
        "ATR(14)":     round(atr, 2),
    }

    # ── Signale bewerten ──
    signals = {}
    score = 0

    # 1. Trend: SMA-Staffel
    if current_price > sma20 > sma50 > sma200:
        signals["Trend (SMA-Staffel)"] = ("↑ Bullish", +1)
        score += 1
    elif current_price < sma20 < sma50 < sma200:
        signals["Trend (SMA-Staffel)"] = ("↓ Bearish", -1)
        score -= 1
    else:
        signals["Trend (SMA-Staffel)"] = ("→ Neutral", 0)

    # 2. Kurzfrist-Trend: Kurs vs. SMA50
    if current_price > sma50:
        signals["Kurs > SMA50"] = ("↑ Bullish", +1)
        score += 1
    elif current_price < sma50:
        signals["Kurs < SMA50"] = ("↓ Bearish", -1)
        score -= 1
    else:
        signals["Kurs = SMA50"] = ("→ Neutral", 0)

    # 3. RSI
    if rsi < 35:
        signals["RSI"] = (f"↑ Überverkauft ({rsi:.1f})", +1)
        score += 1
    elif rsi > 65:
        signals["RSI"] = (f"↓ Überkauft ({rsi:.1f})", -1)
        score -= 1
    else:
        signals["RSI"] = (f"→ Neutral ({rsi:.1f})", 0)

    # 4. MACD
    if macd_val > signal_val and hist_val > 0:
        signals["MACD"] = ("↑ Bullish (über Signal)", +1)
        score += 1
    elif macd_val < signal_val and hist_val < 0:
        signals["MACD"] = ("↓ Bearish (unter Signal)", -1)
        score -= 1
    else:
        signals["MACD"] = ("→ Neutral", 0)

    # 5. Bollinger Bänder
    bb_width = bb_up - bb_lo
    bb_pct   = (current_price - bb_lo) / bb_width if bb_width > 0 else 0.5
    if bb_pct < 0.20:
        signals["Bollinger"] = (f"↑ Unteres Band ({bb_pct:.0%})", +1)
        score += 1
    elif bb_pct > 0.80:
        signals["Bollinger"] = (f"↓ Oberes Band ({bb_pct:.0%})", -1)
        score -= 1
    else:
        signals["Bollinger"] = (f"→ Mittelfeld ({bb_pct:.0%})", 0)

    recommendation = _score_to_recommendation(score)

    return AnalysisResult(
        symbol=symbol,
        name=name,
        current_price=current_price,
        currency=currency,
        score=score,
        recommendation=recommendation,
        signals=signals,
        indicators=indicators,
    )
