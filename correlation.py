"""
Korrelationsanalyse: Wirtschaftsparameter vs. Aktienkurse

Methodik:
  1. Alle Zeitreihen auf monatliche Frequenz resampeln (letzter Wert im Monat)
  2. Für jeden Wirtschaftsparameter und jede Aktie: Pearson-Korrelation mit
     Lags von 0 bis MAX_LAG_MONTHS Monaten berechnen
     (positiver Lag = Wirtschaftsdaten laufen den Aktienkursen voraus)
  3. Den Lag mit der stärksten absoluten Korrelation ermitteln
  4. Ergebnisse sortiert nach Korrelationsstärke ausgeben
"""

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich import box

from database import load_stock_prices, load_economic_series
from data_fetcher import ECONOMIC_PARAMS, TARGET_STOCKS

console = Console()

MAX_LAG_MONTHS = 12   # Vorlauf bis zu 12 Monate testen
MIN_PERIODS    = 36   # Mindestens 3 Jahre gemeinsame Datenpunkte


# ─── Kernfunktion ────────────────────────────────────────────────────────────────

def _monthly_close(df: pd.DataFrame) -> pd.Series:
    """Schlusskurs auf Monatsbasis (letzter Handelstag)."""
    return df["Close"].resample("ME").last().dropna()


def _monthly_series(s: pd.Series) -> pd.Series:
    """Beliebige Zeitreihe auf Monatsbasis (letzter Wert im Monat)."""
    return s.resample("ME").last().dropna()


def lagged_correlation(stock_monthly: pd.Series, eco_monthly: pd.Series,
                       max_lag: int = MAX_LAG_MONTHS) -> pd.Series:
    """
    Berechnet Pearson-Korrelation für Lags 0..max_lag.
    Lag k: eco wird um k Monate *nach vorne* verschoben →
           eco(t-k) korreliert mit stock(t)
           d.h. eco läuft der Aktie um k Monate voraus.

    Gibt eine Series (lag → correlation) zurück.
    """
    corrs = {}
    for lag in range(0, max_lag + 1):
        eco_shifted = eco_monthly.shift(lag)        # eco k Monate in die Zukunft schieben
        combined = pd.concat([stock_monthly, eco_shifted], axis=1).dropna()
        if len(combined) < MIN_PERIODS:
            corrs[lag] = np.nan
            continue
        corrs[lag] = combined.iloc[:, 0].corr(combined.iloc[:, 1])
    return pd.Series(corrs)


def run_correlation_analysis() -> pd.DataFrame:
    """
    Führt die vollständige Korrelationsanalyse für alle Aktie-×-Makro-Kombinationen durch.
    Gibt einen DataFrame mit den stärksten Korrelationen zurück.
    """
    # ── Aktienkurse laden ──
    stock_data = {}
    for symbol in TARGET_STOCKS:
        df = load_stock_prices(symbol)
        if df.empty:
            console.print(f"[yellow]  Keine DB-Daten für {symbol} – zuerst --update-db ausführen[/yellow]")
            continue
        stock_data[symbol] = _monthly_close(df)

    if not stock_data:
        return pd.DataFrame()

    # ── Wirtschaftsparameter laden ──
    eco_data = {}
    for name, meta in ECONOMIC_PARAMS.items():
        s = load_economic_series(meta["ticker"])
        if s.empty:
            continue
        eco_data[name] = _monthly_series(s)

    if not eco_data:
        console.print("[yellow]Keine Makrodaten in DB. Zuerst --update-db ausführen.[/yellow]")
        return pd.DataFrame()

    # ── Korrelationen berechnen ──
    results = []
    total = len(stock_data) * len(eco_data)
    done  = 0

    with console.status(f"[bold green]Berechne Korrelationen (0/{total})…[/bold green]") as status:
        for symbol, stock_series in stock_data.items():
            for eco_name, eco_series in eco_data.items():
                done += 1
                status.update(f"[bold green]Berechne Korrelationen ({done}/{total})…[/bold green]")

                corr_by_lag = lagged_correlation(stock_series, eco_series)
                if corr_by_lag.dropna().empty:
                    continue

                best_lag  = int(corr_by_lag.abs().idxmax())
                best_corr = corr_by_lag[best_lag]

                results.append({
                    "Aktie":       symbol,
                    "Makro":       eco_name,
                    "Ticker":      ECONOMIC_PARAMS[eco_name]["ticker"],
                    "Korr@Lag0":   round(corr_by_lag[0], 3),
                    "Bester Lag":  best_lag,
                    "Max |Korr|":  round(abs(best_corr), 3),
                    "Korrelation": round(best_corr, 3),
                    "Richtung":    "positiv" if best_corr > 0 else "negativ",
                })

    return pd.DataFrame(results)


# ─── Ausgabe ─────────────────────────────────────────────────────────────────────

def _corr_color(val: float) -> str:
    a = abs(val)
    if a >= 0.7:
        return "bold green" if val > 0 else "bold red"
    elif a >= 0.5:
        return "green" if val > 0 else "red"
    elif a >= 0.3:
        return "yellow"
    return "dim"


def print_correlation_report(df: pd.DataFrame):
    if df.empty:
        console.print("[yellow]Keine Ergebnisse.[/yellow]")
        return

    from rich.panel import Panel
    console.print(Panel.fit(
        "[bold cyan]Korrelationsanalyse: Wirtschaftsdaten → Aktienkurse[/bold cyan]\n"
        "[dim]Lag = Monate, um die der Wirtschaftsindikator der Aktie vorausläuft (0 = gleichzeitig)[/dim]",
        box=box.DOUBLE_EDGE,
    ))

    for symbol in df["Aktie"].unique():
        sub = (df[df["Aktie"] == symbol]
               .sort_values("Max |Korr|", ascending=False)
               .head(15))

        table = Table(
            box=box.SIMPLE_HEAD,
            header_style="bold blue",
            title=f"[bold cyan]{symbol}[/bold cyan] – Top-Korrelationen",
            expand=True,
        )
        table.add_column("Wirtschaftsparameter", min_width=22)
        table.add_column("Ticker",   style="dim",    width=22)
        table.add_column("Lag (Mo)", justify="center", width=9)
        table.add_column("Korr@0",  justify="right",  width=9)
        table.add_column("Max|Korr|",justify="right", width=10)
        table.add_column("Korrelation", justify="right", width=12)
        table.add_column("Vorzeichen", width=10)

        for _, row in sub.iterrows():
            color = _corr_color(row["Korrelation"])
            table.add_row(
                row["Makro"],
                row["Ticker"],
                str(row["Bester Lag"]),
                str(row["Korr@Lag0"]),
                str(row["Max |Korr|"]),
                f"[{color}]{row['Korrelation']:+.3f}[/{color}]",
                f"[{color}]{row['Richtung']}[/{color}]",
            )

        console.print(table)

    # ── Globale Führungsindikatoren ──
    leading = (df[df["Bester Lag"] >= 2]
               .sort_values("Max |Korr|", ascending=False)
               .drop_duplicates(subset=["Makro"])
               .head(10))

    if not leading.empty:
        console.print()
        lt = Table(
            box=box.ROUNDED,
            header_style="bold magenta",
            title="[bold]Top Führungsindikatoren (Lag ≥ 2 Monate)[/bold]",
            caption="Diese Makrodaten laufen mehreren Aktienkursen zeitlich voraus",
        )
        lt.add_column("Wirtschaftsparameter", min_width=22)
        lt.add_column("Ticker",    style="dim",     width=22)
        lt.add_column("Aktie",     width=8)
        lt.add_column("Lag (Mo)",  justify="center", width=9)
        lt.add_column("Korrelation", justify="right", width=12)

        for _, row in leading.iterrows():
            color = _corr_color(row["Korrelation"])
            lt.add_row(
                row["Makro"],
                row["Ticker"],
                row["Aktie"],
                str(row["Bester Lag"]),
                f"[{color}]{row['Korrelation']:+.3f}[/{color}]",
            )
        console.print(lt)

    # ── CSV-Export ──
    out_path = Path(__file__).parent / "korrelationen.csv"
    df.sort_values(["Aktie", "Max |Korr|"], ascending=[True, False]).to_csv(out_path, index=False)
    console.print(f"\n[dim]Vollständige Ergebnisse gespeichert: {out_path}[/dim]")


from pathlib import Path
