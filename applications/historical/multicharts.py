"""MultiCharts CSV exports -> bronze/multicharts_ohlcv -> silver/multicharts_ohlcv.

Reads data/multicharts/<file>.csv written by the ExportBars indicator
(see the connector docstring) and merges the bars into bronze, then copies
into silver (clean_ohlcv) every bronze bar newer than the last silver one,
so an existing bronze is backfilled into silver on the first run.
Gold is built by applications/historical/ohlcv_gold.py.

Three modes:
  (default)  incremental: only bars after the last stored one. Bars missing
             in the past (e.g. a session-template hole) are never added.
  --full     re-reads the whole CSV and overwrites every bar it contains
             (connector change, or the back-adjusted continuous shifted at a
             rollover). Rows that are only in the old data stay as they were.
  --replace  the new export replaces the old one entirely: deletes the
             symbol from bronze, silver and every gold/multicharts_ohlcv/<tf>,
             then loads the CSV. Use it after re-exporting @ES / @NQ (new
             session template, different history start): with --full old-only
             rows would keep the old back-adjustment, and ohlcv_gold.py, which
             is incremental, would never rebuild past windows. Run
             ohlcv_gold.py afterwards: it rebuilds the gold from scratch.

Run:
    .venv/bin/python applications/historical/multicharts.py [--full | --replace]
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
import quantlake.silver.ingest as silver
from quantlake.bronze.connectors.multicharts import MC_DIR, MultiChartsCSVConnector
from quantlake.config import BRONZE_ROOT, GOLD_ROOT, SILVER_ROOT
from quantlake.maintenance import find_tables
from quantlake.silver.gaps import early_fridays, recurring_gaps
from quantlake.storage import delete_symbol, last_timestamp, read_symbol
from symbols import MC_FILES

TABLE = MultiChartsCSVConnector.TABLE_NAME


def sync_silver(symbol: str, full: bool = False) -> None:
    last = None if full else last_timestamp(str(SILVER_ROOT / TABLE), symbol)
    since = last + timedelta(minutes=1) if last else None
    df = read_symbol(str(BRONZE_ROOT / TABLE), symbol, since=since)
    if df is None or df.is_empty():
        return
    silver.ingest(df.sort("timestamp"), TABLE, align_1m=True, update_matched=full)
    print(f"[{symbol}] silver +{len(df):,} bars")


def ingest_csv(f, full: bool = False, folder: Path | None = None) -> bool:
    connector = MultiChartsCSVConnector(chart_tz=f.chart_tz, **({"folder": folder} if folder else {}))
    if not (connector.folder / f"{f.file}.csv").exists():
        print(f"[{f.symbol}] {f.file}.csv not found in {connector.folder}")
        return False
    last = None if full else bronze.last_bronze_ts(TABLE, f.symbol)
    df = connector.fetch(symbol=f.file, start=last + timedelta(minutes=1) if last else None)
    if df.is_empty():
        print(f"[{f.symbol}] bronze up to date")
        return True
    df = bronze.add_partition_columns(df, symbol=f.symbol)
    bronze.save(df, TABLE, update_matched=full)
    print(f"[{f.symbol}] bronze +{len(df):,} bars, {df['timestamp'].min()} -> {df['timestamp'].max()}")
    return True


def drop_symbol(symbol: str) -> None:
    """--replace: remove symbol from bronze, silver and every gold/multicharts_ohlcv/<tf>."""
    paths = [BRONZE_ROOT / TABLE, SILVER_ROOT / TABLE, *find_tables(GOLD_ROOT / TABLE)]
    deleted = {f"{p.parent.name}/{p.name}": delete_symbol(str(p), symbol) for p in paths}
    print(f"[{symbol}] deleted " + ", ".join(f"{k} {v:,}" for k, v in deleted.items()))


def report_session_problems(symbol: str) -> None:
    """Flag holes that repeat at the same time of day and Fridays ending early (session template)."""
    bars = read_symbol(str(SILVER_ROOT / TABLE), symbol, columns=["timestamp"])
    if bars is None or bars.is_empty():
        return
    recurring, fridays = recurring_gaps(bars), early_fridays(bars)
    if recurring.is_empty() and fridays.is_empty():
        return
    print(f"[{symbol}] WARNING session template? recurring holes: {recurring.height} month-windows, "
          f"Fridays ending before 15:59 CT: {fridays.height} months "
          f"(details: applications/diagnostics/multicharts_gaps.py {symbol})")


def main(argv: list[str], folder: Path | None = None) -> None:
    replace = "--replace" in argv
    full = replace or "--full" in argv
    for f in MC_FILES:
        if replace:
            if not ((folder or MC_DIR) / f"{f.file}.csv").exists():
                print(f"[{f.symbol}] {f.file}.csv not found: nothing replaced")
                continue
            drop_symbol(f.symbol)
        ingest_csv(f, full=full, folder=folder)
        sync_silver(f.symbol, full=full)  # also when the CSV is missing: bronze may already hold bars
        report_session_problems(f.symbol)


if __name__ == "__main__":
    main(sys.argv[1:])
