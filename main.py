#!/usr/bin/env python3
"""
Wirtschaftstool – Hauptprogramm
================================
Zeigt:
  1. Aktuelle Wirtschaftsparameter (Rohstoffe, Indizes, FX, Renditen …)
  2. Kauf-/Verkaufsempfehlungen für DBK, SIE, ALV, DTE, RGLD, AMZN, BNP
  3. Datenbankupdate (20 Jahre Historie, inkrementell)
  4. Korrelationsanalyse Makro → Aktien

Verwendung:
  python main.py               # Vollständige Live-Ausgabe
  python main.py --stocks      # Nur Aktienempfehlungen (live)
  python main.py --macro       # Nur Makrodaten (live)
  python main.py --update-db   # Datenbank aktualisieren
  python main.py --db-info     # Datenbankinhalt anzeigen
  python main.py --correlations # Korrelationsanalyse
"""

import argparse
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text

from data_fetcher import (
    fetch_all_economic_params,
    fetch_stock_history,
    TARGET_STOCKS,
)
from analyzer import analyze

console = Console()

# ─── Farb-Mapping ───────────────────────────────────────────────────────────────

RECOMMENDATION_COLORS = {
    "STRONG BUY":  "bold green",
    "BUY":         "green",
    "HOLD":        "yellow",
    "SELL":        "red",
    "STRONG SELL": "bold red",
}

RECOMMENDATION_ICONS = {
    "STRONG BUY":  "▲▲",
    "BUY":         "▲",
    "HOLD":        "◆",
    "SELL":        "▼",
    "STRONG SELL": "▼▼",
}


# ─── Ausgabe-Funktionen ─────────────────────────────────────────────────────────

def print_macro_table():
    console.print(Panel.fit(
        "[bold cyan]Makroökonomische Übersicht[/bold cyan]",
        box=box.DOUBLE_EDGE
    ))

    with console.status("[bold green]Lade Wirtschaftsdaten…[/bold green]"):
        df = fetch_all_economic_params()

    table = Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold blue",
        title="[bold]30 wichtigste Wirtschaftsparameter[/bold]",
        caption="Quellen: Yahoo Finance / FRED",
        expand=True,
    )
    table.add_column("#",          style="dim", width=3)
    table.add_column("Parameter",  min_width=20)
    table.add_column("Ticker",     style="cyan", min_width=22)
    table.add_column("Raum",       min_width=8)
    table.add_column("Aktuell",    justify="right", min_width=14)
    table.add_column("Quelle",     style="dim", min_width=8)

    for i, row in df.iterrows():
        val = str(row["Aktuell"])
        val_style = "white" if val == "N/A" else "bold white"
        table.add_row(
            str(i + 1),
            row["Parameter"],
            row["Ticker"],
            row["Raum"],
            Text(val, style=val_style),
            row["Quelle"],
        )

    console.print(table)
    console.print()


def print_stock_recommendations():
    console.print(Panel.fit(
        "[bold cyan]Aktienempfehlungen[/bold cyan]",
        box=box.DOUBLE_EDGE
    ))

    results = []
    for symbol, meta in TARGET_STOCKS.items():
        with console.status(f"[bold green]Analysiere {symbol} ({meta['name']})…[/bold green]"):
            hist = fetch_stock_history(symbol, period="1y")

        if hist is None or hist.empty or len(hist) < 50:
            console.print(f"[yellow]  ⚠  Keine ausreichenden Daten für {symbol}[/yellow]")
            continue

        # Währung bestimmen
        currency = "EUR" if meta["exchange"] in ("XETRA", "Euronext") else "USD"

        result = analyze(symbol, meta["name"], hist, currency=currency)
        results.append(result)

        # ── Detailausgabe ──
        color = RECOMMENDATION_COLORS.get(result.recommendation, "white")
        icon  = RECOMMENDATION_ICONS.get(result.recommendation, "")

        console.print(Panel(
            _build_detail_text(result),
            title=f"[bold]{icon} {symbol} – {meta['name']}[/bold]",
            border_style=color,
            expand=False,
        ))

    # ── Zusammenfassung ──
    if results:
        console.print()
        summary = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold blue",
            title="[bold]Empfehlungs-Zusammenfassung[/bold]",
        )
        summary.add_column("Symbol", style="bold cyan", width=8)
        summary.add_column("Name",   min_width=20)
        summary.add_column("Kurs",   justify="right", width=12)
        summary.add_column("Score",  justify="center", width=7)
        summary.add_column("Empfehlung", min_width=14)

        for r in results:
            color = RECOMMENDATION_COLORS.get(r.recommendation, "white")
            icon  = RECOMMENDATION_ICONS.get(r.recommendation, "")
            price_str = f"{r.current_price:.2f} {r.currency}" if r.current_price else "N/A"
            summary.add_row(
                r.symbol,
                r.name,
                price_str,
                str(r.score),
                Text(f"{icon} {r.recommendation}", style=color),
            )

        console.print(summary)


def _build_detail_text(result) -> str:
    lines = []

    price_str = f"{result.current_price:.2f} {result.currency}" if result.current_price else "N/A"
    lines.append(f"[dim]Aktueller Kurs:[/dim] [bold white]{price_str}[/bold white]")
    lines.append("")

    # Indikatoren
    lines.append("[dim]── Indikatoren ──────────────────────[/dim]")
    for key, val in result.indicators.items():
        lines.append(f"  [dim]{key:<14}[/dim] {val}")
    lines.append("")

    # Signale
    lines.append("[dim]── Signale ───────────────────────────[/dim]")
    for key, (desc, pts) in result.signals.items():
        pt_str = f"[green]+{pts}[/green]" if pts > 0 else (f"[red]{pts}[/red]" if pts < 0 else "[yellow]0[/yellow]")
        lines.append(f"  {desc:<40} {pt_str}")
    lines.append("")

    # Gesamtergebnis
    color = RECOMMENDATION_COLORS.get(result.recommendation, "white")
    icon  = RECOMMENDATION_ICONS.get(result.recommendation, "")
    lines.append(
        f"[dim]Score:[/dim] [bold]{result.score:+d}[/bold]   "
        f"[dim]Empfehlung:[/dim] [{color}][bold]{icon} {result.recommendation}[/bold][/{color}]"
    )

    return "\n".join(lines)


# ─── Datenbank-Ausgabe ──────────────────────────────────────────────────────────

def print_db_info():
    from database import db_summary
    from rich.panel import Panel

    console.print(Panel.fit("[bold cyan]Datenbankinhalt[/bold cyan]", box=box.DOUBLE_EDGE))
    df = db_summary()
    if df.empty:
        console.print("[yellow]Datenbank ist leer. Zuerst --update-db ausführen.[/yellow]")
        return

    table = Table(box=box.SIMPLE_HEAD, header_style="bold blue", expand=True)
    table.add_column("Typ",     width=7)
    table.add_column("Ticker",  min_width=24)
    table.add_column("Zeilen",  justify="right", width=8)
    table.add_column("Von",     width=12)
    table.add_column("Bis",     width=12)

    for _, row in df.iterrows():
        table.add_row(row["typ"], row["ticker"], str(row["rows"]), row["von"], row["bis"])
    console.print(table)


def run_db_update():
    from database import update_all_stocks, update_all_economic
    from rich.panel import Panel

    console.print(Panel.fit("[bold cyan]Datenbankupdate[/bold cyan]", box=box.DOUBLE_EDGE))

    console.print("[bold]Wirtschaftsparameter…[/bold]")
    eco_res = update_all_economic()
    eco_new = sum(eco_res.values())
    console.print(f"  [green]{eco_new} neue Datenpunkte[/green] für {len(eco_res)} Zeitreihen\n")

    console.print("[bold]Aktienkurse…[/bold]")
    stk_res = update_all_stocks()
    stk_new = sum(stk_res.values())
    console.print(f"  [green]{stk_new} neue Datenpunkte[/green] für {len(stk_res)} Aktien\n")

    details = Table(box=box.SIMPLE_HEAD, header_style="bold blue")
    details.add_column("Ticker", min_width=10)
    details.add_column("Neue Zeilen", justify="right", width=14)
    for ticker, n in {**eco_res, **stk_res}.items():
        details.add_row(ticker, str(n))
    console.print(details)


# ─── Einstiegspunkt ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Wirtschaftstool – Makrodaten & Aktienempfehlungen"
    )
    parser.add_argument("--stocks",       action="store_true", help="Nur Aktienempfehlungen (live)")
    parser.add_argument("--macro",        action="store_true", help="Nur Makrodaten (live)")
    parser.add_argument("--update-db",    action="store_true", help="Datenbank aktualisieren (20J Historie)")
    parser.add_argument("--db-info",      action="store_true", help="Datenbankinhalt anzeigen")
    parser.add_argument("--correlations", action="store_true", help="Korrelationsanalyse Makro → Aktien")
    args = parser.parse_args()

    console.rule("[bold blue]Wirtschaftstool[/bold blue]")

    if args.update_db:
        run_db_update()
    elif args.db_info:
        print_db_info()
    elif args.correlations:
        from correlation import run_correlation_analysis, print_correlation_report
        df = run_correlation_analysis()
        print_correlation_report(df)
    else:
        show_macro  = args.macro  or not (args.stocks or args.macro)
        show_stocks = args.stocks or not (args.stocks or args.macro)
        if show_macro:
            print_macro_table()
        if show_stocks:
            print_stock_recommendations()

    console.rule()


if __name__ == "__main__":
    main()
