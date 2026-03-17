#!/usr/bin/env python3
"""
Wirtschaftstool – Hauptprogramm
================================
Zeigt:
  1. Aktuelle Wirtschaftsparameter (Rohstoffe, Indizes, FX, Renditen …)
  2. Kauf-/Verkaufsempfehlungen für DBK, SIE, ALV, DTE, RGLD, AMZN, BNP

Verwendung:
  python main.py            # Vollständige Ausgabe
  python main.py --stocks   # Nur Aktienempfehlungen
  python main.py --macro    # Nur Makrodaten
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


# ─── Einstiegspunkt ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Wirtschaftstool – Makrodaten & Aktienempfehlungen"
    )
    parser.add_argument("--stocks", action="store_true", help="Nur Aktienempfehlungen anzeigen")
    parser.add_argument("--macro",  action="store_true", help="Nur Makrodaten anzeigen")
    args = parser.parse_args()

    show_macro  = args.macro  or not (args.stocks or args.macro)
    show_stocks = args.stocks or not (args.stocks or args.macro)

    console.rule("[bold blue]Wirtschaftstool[/bold blue]")

    if show_macro:
        print_macro_table()

    if show_stocks:
        print_stock_recommendations()

    console.rule()


if __name__ == "__main__":
    main()
