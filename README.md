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

### Bewertungsmaßstäbe und Gewichtung

Die Empfehlung basiert auf **5 gleichgewichteten technischen Signalen**. Jedes Signal
liefert einen Punktwert: **+1** (bullisches Signal), **0** (neutral), **−1** (bärisches Signal).
Die Punkte werden addiert; der Gesamtscore bestimmt die Empfehlung.

---

#### Signal 1 – Trendstruktur: SMA-Staffel (Gewicht: 1 Punkt)
Gleitende Durchschnitte über 20, 50 und 200 Handelstage.

| Bedingung | Bewertung |
|-----------|-----------|
| Kurs > SMA20 > SMA50 > SMA200 | +1 Aufwärtstrend intakt |
| Kurs < SMA20 < SMA50 < SMA200 | −1 Abwärtstrend intakt |
| Sonstige Konstellation | 0 uneinheitlich |

> Warum: Die SMA-Staffel zeigt, ob kurz-, mittel- und langfristiger Trend
> gleichgerichtet sind. Gilt als zuverlässigstes Trendsignal.

---

#### Signal 2 – Kurzfrist-Trend: Kurs vs. SMA50 (Gewicht: 1 Punkt)
Der 50-Tage-Durchschnitt trennt kurzfristige Aufwärts- von Abwärtsphasen.

| Bedingung | Bewertung |
|-----------|-----------|
| Kurs > SMA50 | +1 bullisch |
| Kurs < SMA50 | −1 bärisch |

> Warum: Der SMA50 wird von institutionellen Marktteilnehmern als wichtige
> Unterstützungs-/Widerstandslinie beobachtet.

---

#### Signal 3 – Momentum: RSI 14 (Gewicht: 1 Punkt)
Der Relative Strength Index misst, ob eine Aktie überkauft oder überverkauft ist.
Berechnung über 14 Handelstage.

| RSI-Wert | Bewertung |
|----------|-----------|
| < 35 | +1 überverkauft → Kaufgelegenheit |
| 35 – 65 | 0 neutral |
| > 65 | −1 überkauft → Verkaufsdruck |

> Warum: Extremwerte des RSI signalisieren häufig eine bevorstehende Gegenbewegung
> (Mean Reversion). Die Schwellen 35/65 sind etwas enger als klassisch (30/70),
> um früher zu reagieren.

---

#### Signal 4 – Momentum: MACD 12/26/9 (Gewicht: 1 Punkt)
Der Moving Average Convergence/Divergence-Indikator misst die Dynamik des Trends.

| Bedingung | Bewertung |
|-----------|-----------|
| MACD-Linie > Signallinie **und** Histogramm > 0 | +1 Aufwärtsmomentum |
| MACD-Linie < Signallinie **und** Histogramm < 0 | −1 Abwärtsmomentum |
| Sonstige | 0 neutral |

> Berechnungsgrundlage: EMA12 − EMA26 = MACD-Linie; EMA9 der MACD-Linie =
> Signallinie; Differenz = Histogramm. Beide Bedingungen müssen erfüllt sein,
> um Fehlsignale zu reduzieren.

---

#### Signal 5 – Relative Kursposition: Bollinger Bänder (Gewicht: 1 Punkt)
Die Bollinger Bänder (20 Tage, ±2 Standardabweichungen) zeigen, wo der Kurs
innerhalb seiner jüngsten Schwankungsbreite steht.

| Position | Bewertung |
|----------|-----------|
| Kurs im untersten 20 %-Bereich (nahe unterem Band) | +1 günstig bewertet |
| Kurs im obersten 20 %-Bereich (nahe oberem Band) | −1 teuer bewertet |
| Kurs im mittleren Bereich (20 %–80 %) | 0 neutral |

> Warum: Kurse nahe dem unteren Bollinger Band sind statistisch selten und deuten
> auf übertriebenen Verkaufsdruck hin – und umgekehrt.

---

#### Gesamtscore und Empfehlung

| Score | Empfehlung  | Bedeutung |
|-------|-------------|-----------|
| ≥ +3  | STRONG BUY  | Mindestens 3 von 5 Signalen bullisch, keines stark bärisch |
| +1/+2 | BUY         | Überwiegend bullische Signale |
| 0     | HOLD        | Ausgeglichenes Bild, abwarten |
| −1/−2 | SELL        | Überwiegend bärische Signale |
| ≤ −3  | STRONG SELL | Mindestens 3 von 5 Signalen bärisch |

**Hinweise zur Interpretation:**
- Alle 5 Signale sind **gleichgewichtet** (je 1 Punkt). Es findet keine
  fundamentale Bewertung (KGV, Dividende, Umsatz) statt.
- Die Analyse basiert auf **1 Jahr Kursdaten** (ca. 252 Handelstage).
- Der ATR (Average True Range, 14 Tage) wird als Volatilitätsmaß zusätzlich
  angezeigt, fließt aber **nicht** in den Score ein – er dient der
  Einschätzung des Risikos (je höher der ATR, desto größer die Tagesschwankungen).
- Die Empfehlungen sind rein technischer Natur und **kein Anlageberatung**.

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
