#!/usr/bin/env python3
"""Statistiche del journal discrezionale (solo libreria standard).

Uso:
    python3 journal_stats.py            # legge trades.csv nella stessa cartella
    python3 journal_stats.py altro.csv

Per ogni trade chiuso calcola l'esito in R (profitto / rischio iniziale).
Se la colonna result_r e' vuota, R viene ricavato da entry/stop/exit:
    long : R = (exit - entry) / (entry - stop)
    short: R = (entry - exit) / (stop - entry)
I trade senza exit e senza result_r sono considerati aperti e ignorati.
"""
import csv
import os
import sys
from collections import defaultdict

MIN_SAMPLE = 50   # sotto questa soglia il report avvisa che il campione e' piccolo


def to_float(value):
    value = (value or "").strip().replace(",", ".")
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def result_in_r(row):
    """Esito in R del trade, oppure None se aperto / non calcolabile."""
    r = to_float(row.get("result_r"))
    if r is not None:
        return r
    entry, stop, exit_ = (to_float(row.get(k)) for k in ("entry", "stop", "exit"))
    if entry is None or stop is None or exit_ is None:
        return None
    risk = abs(entry - stop)
    if risk == 0:
        return None
    direction = (row.get("direction") or "").strip().lower()
    if direction == "short":
        return (entry - exit_) / risk
    return (exit_ - entry) / risk


def stats(rs):
    """Metriche di base su una lista di esiti in R."""
    n = len(rs)
    if n == 0:
        return None
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    # max drawdown sulla curva cumulata in R
    peak = cum = 0.0
    max_dd = 0.0
    for r in rs:
        cum += r
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return {
        "n": n,
        "hit": len(wins) / n,
        "avg_r": sum(rs) / n,
        "avg_win": (gross_win / len(wins)) if wins else 0.0,
        "avg_loss": (-gross_loss / len(losses)) if losses else 0.0,
        "pf": (gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "total_r": sum(rs),
        "max_dd": max_dd,
    }


def fmt_row(label, s):
    pf = "inf" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
    return (f"{label:<14} {s['n']:>4} {s['hit']*100:>6.1f}% {s['avg_r']:>+7.2f} "
            f"{s['avg_win']:>+7.2f} {s['avg_loss']:>+7.2f} {pf:>6} "
            f"{s['total_r']:>+8.2f} {s['max_dd']:>7.2f}")


HEADER = (f"{'gruppo':<14} {'n':>4} {'hit%':>7} {'R medio':>7} "
          f"{'R win':>7} {'R loss':>7} {'PF':>6} {'R tot':>8} {'maxDD':>7}")


def print_group(title, groups):
    print(f"\n--- per {title} ---")
    print(HEADER)
    for key in sorted(groups):
        s = stats(groups[key])
        if s:
            print(fmt_row(key or "(vuoto)", s))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "trades.csv")
    if not os.path.exists(path):
        sys.exit(f"File non trovato: {path}")

    closed, open_count = [], 0
    by = {"category": defaultdict(list), "confidence": defaultdict(list),
          "horizon": defaultdict(list), "direction": defaultdict(list),
          "instrument": defaultdict(list)}

    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not any((v or "").strip() for v in row.values()):
                continue                       # riga vuota
            r = result_in_r(row)
            if r is None:
                open_count += 1
                continue
            closed.append(r)
            for field, groups in by.items():
                groups[(row.get(field) or "").strip().lower()].append(r)

    print(f"Journal: {path}")
    print(f"Trade chiusi: {len(closed)}   aperti/non calcolabili: {open_count}")
    if not closed:
        print("Nessun trade chiuso da analizzare.")
        return
    if len(closed) < MIN_SAMPLE:
        print(f"ATTENZIONE: campione piccolo ({len(closed)} < {MIN_SAMPLE}): "
              "le statistiche non sono ancora affidabili.")

    print("\n--- totale ---")
    print(HEADER)
    print(fmt_row("tutti", stats(closed)))

    for field, title in (("category", "categoria"), ("confidence", "confidenza"),
                         ("horizon", "orizzonte"), ("direction", "direzione"),
                         ("instrument", "strumento")):
        print_group(title, by[field])

    print("\nLegenda: R = profitto/rischio iniziale; PF = R vinti / R persi; "
          "maxDD = massimo drawdown della curva cumulata in R.")


if __name__ == "__main__":
    main()
