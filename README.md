# Wirtschaftstool

Kommandozeilen-Tool zur Anzeige aktueller makroökonomischer Kennzahlen sowie
technischer Kauf-/Verkaufsempfehlungen für ausgewählte Aktien.

---

## Funktionen

### 1. Makroökonomische Übersicht (30 Parameter)
Ruft live-Daten ab für:
- **Rohstoffe:** WTI-Öl, Brent-Öl, Gold, Silber, Kupfer, Erdgas, Platin, Palladium
- **Indizes:** DAX, Euro Stoxx 50, CAC 40, S&P 500, Dow Jones, NASDAQ 100, FTSE 100
- **Volatilität:** VIX (USD-Raum), VSTOXX / V2TX (EUR-Raum)
- **Wechselkurse:** EUR/USD, GBP/USD, USD/JPY, USD/CHF, USD/CNY, USD-Index
- **Anleiherenditen:** US 5J, 10J, 30J Treasury Yields
- **ETF:** MSCI World (URTH)
- **Krypto:** Bitcoin
- **Inflation:** US CPI und EU HICP (via FRED API)

### 2. Aktienempfehlungen
Technische Analyse für folgende Titel:

| Kürzel | Name              | Börse    |
|--------|-------------------|----------|
| DBK    | Deutsche Bank     | XETRA    |
| SIE    | Siemens           | XETRA    |
| ALV    | Allianz           | XETRA    |
| DTE    | Deutsche Telekom  | XETRA    |
| RGLD   | Royal Gold        | NASDAQ   |
| AMZN   | Amazon            | NASDAQ   |
| BNP    | BNP Paribas       | Euronext |

**Verwendete Indikatoren:**
- SMA 20 / 50 / 200 (Gleitende Durchschnitte)
- RSI 14 (Relative Strength Index)
- MACD 12/26/9
- Bollinger Bänder (20 Perioden, ±2σ)
- ATR 14 (Average True Range, als Volatilitätsmaß)

**Scoring-System:** Jeder Indikator liefert +1 (bullish), 0 (neutral) oder −1 (bearish).

| Score  | Empfehlung   |
|--------|--------------|
| ≥ +3   | STRONG BUY   |
| +1/+2  | BUY          |
| 0      | HOLD         |
| −1/−2  | SELL         |
| ≤ −3   | STRONG SELL  |

---

## Installation

### Voraussetzungen
- Python 3.9 oder neuer
- pip

### Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Installierte Pakete:
- `yfinance` — Marktdaten von Yahoo Finance
- `pandas` — Datenverarbeitung
- `pandas-datareader` — zusätzliche Datenquellen
- `ta` — Technische-Analyse-Bibliothek
- `rich` — formatierte Terminal-Ausgabe
- `requests` — HTTP-Anfragen
- `fredapi` — FRED-API-Anbindung (US-Wirtschaftsdaten)

### FRED API Key (für Inflationsdaten)

Kostenlosen API-Key registrieren unter:
https://fred.stlouisfed.org/docs/api/api_key.html

Den Key in eine Datei `fred_API_Key.txt` im Projektverzeichnis schreiben:

```
API Key: <dein-key>
```

Ohne diesen Key werden die Inflationswerte (US CPI, EU HICP) als `N/A` angezeigt.
Alle anderen Daten funktionieren ohne Key.

---

## Aufruf

```bash
# Vollständige Ausgabe: Makrodaten + Aktienempfehlungen
python main.py

# Nur Aktienempfehlungen
python main.py --stocks

# Nur Makroökonomische Übersicht
python main.py --macro
```

---

## Projektstruktur

```
Wirtschaftstool/
├── main.py          # Einstiegspunkt, Terminal-Ausgabe (rich)
├── data_fetcher.py  # Datenabruf: yfinance + FRED API
├── analyzer.py      # Technische Indikatoren & Scoring
├── requirements.txt # Python-Abhängigkeiten
├── README.md        # Diese Datei
└── .gitignore       # Schützt Schlüsseldateien vor Git-Commits
```

> **Hinweis:** Die Dateien `fred_API_Key.txt` und `Github_Token.txt` sind in
> `.gitignore` eingetragen und werden nicht ins Repository übertragen.
