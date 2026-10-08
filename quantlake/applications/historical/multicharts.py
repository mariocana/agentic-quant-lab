"""MultiCharts CSV exports -> bronze/multicharts_ohlcv -> silver/multicharts_ohlcv.

Reads data/multicharts/<file>.csv written by the ExportBars indicator (see
the connector docstring and applications/MULTICHARTS_EXPORT.md). Per symbol
there are two files (applications/symbols.py, MC_FILES):

  ES_1min.csv    full history, exported once and again after each quarterly
                 roll. Merged into bronze; silver copies every bronze bar newer
                 than the last silver one (an existing bronze is backfilled
                 into silver on the first run).
  ES_recent.csv  a short chart of the last days, exported every morning. Always
                 upserted whole, in bronze and silver (silver rewritten from its
                 first bar): after a quarterly roll the back-adjusted last days
                 move to the new contract, so yesterday's close matches today's
                 prices. Applied after the history file.

Modes for the history file:
  (default)  incremental: only bars after the last stored one. Bars missing
             in the past (e.g. a session-template hole) are never added.
  --full     re-reads the whole CSV and overwrites every bar it contains
             (connector change). Rows that are only in the old data stay as
             they were, with TradeStation's old back-adjustment.
  --replace  the new history export replaces the old one entirely: deletes the
             symbol from bronze, silver and every gold/multicharts_ohlcv/<tf>,
             loads ES_1min.csv, then the recent file as usual. Use it after
             re-exporting the history (quarterly roll, new session template):
             ohlcv_gold.py is incremental and would never rebuild past windows,
             so run it afterwards, it rebuilds the gold from scratch. Without
             the history file nothing is deleted.

After each symbol, recurring holes / early Fridays (silver.gaps) are reported:
a wrong session template.

Run:
    .venv/bin/python applications/historical/multicharts.py [--full | --replace]
"""
import sys
from datetime import datetime, timedelta
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


def sync_silver(symbol: str, full: bool = False, rewrite_from: datetime | None = None) -> None:
    """Copy new bronze bars to silver; from rewrite_from on, overwrite what silver has."""
    last = None if full else last_timestamp(str(SILVER_ROOT / TABLE), symbol)
    since = last + timedelta(minutes=1) if last else None
    if rewrite_from is not None and since is not None:
        since = min(since, rewrite_from)
    df = read_symbol(str(BRONZE_ROOT / TABLE), symbol, since=since)
    if df is None or df.is_empty():
        return
    silver.ingest(df.sort("timestamp"), TABLE, align_1m=True, update_matched=full or rewrite_from is not None)
    print(f"[{symbol}] silver {len(df):,} bars from {df['timestamp'].min()}")


def ingest_csv(f, full: bool = False, folder: Path | None = None) -> datetime | None:
    """Merge one CSV into bronze. A 'recent' file is upserted whole (it is short):
    returns its first timestamp so silver rewrites the same range."""
    connector = MultiChartsCSVConnector(chart_tz=f.chart_tz, **({"folder": folder} if folder else {}))
    if not (connector.folder / f"{f.file}.csv").exists():
        print(f"[{f.symbol}] {f.file}.csv not found in {connector.folder}")
        return None
    rewrite = full or f.recent
    last = None if rewrite else bronze.last_bronze_ts(TABLE, f.symbol)
    df = connector.fetch(symbol=f.file, start=last + timedelta(minutes=1) if last else None)
    if df.is_empty():
        print(f"[{f.symbol}] {f.file}: bronze up to date")
        return None
    df = bronze.add_partition_columns(df, symbol=f.symbol)
    bronze.save(df, TABLE, update_matched=rewrite)
    print(f"[{f.symbol}] {f.file}: bronze {len(df):,} bars, {df['timestamp'].min()} -> {df['timestamp'].max()}")
    return df["timestamp"].min() if f.recent else None


def drop_symbol(symbol: str) -> None:
    """--replace: remove symbol from bronze, silver and every gold/multicharts_ohlcv/<tf>."""
    paths = [BRONZE_ROOT / TABLE, SILVER_ROOT / TABLE, *find_tables(GOLD_ROOT / TABLE)]
    deleted = {f"{p.parent.name}/{p.name}": delete_symbol(str(p), symbol) for p in paths}
    print(f"[{symbol}] deleted " + ", ".join(f"{k} {v:,}" for k, v in deleted.items()))


def report_session_problems(symbol: str) -> None:
    """Flag holes that repeat at the same time of day and Fridays ending early (session template).

    The monthly rules need enough days (see silver.gaps): a few days of
    recent file alone never trigger them.
    """
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
    for symbol in dict.fromkeys(f.symbol for f in MC_FILES):
        files = [f for f in MC_FILES if f.symbol == symbol]
        history = [f for f in files if not f.recent]
        recent = [f for f in files if f.recent]
        full = "--full" in argv
        if replace:
            if history and all(((folder or MC_DIR) / f"{f.file}.csv").exists() for f in history):
                drop_symbol(symbol)
                full = True
            else:
                print(f"[{symbol}] history CSV not found: nothing replaced")
        for f in history:
            ingest_csv(f, full=full, folder=folder)
        starts = [ingest_csv(f, full=full, folder=folder) for f in recent]  # after history: overwrites the last days
        rewrite_from = min((s for s in starts if s is not None), default=None)
        sync_silver(symbol, full=full, rewrite_from=rewrite_from)  # also when the CSVs are missing
        report_session_problems(symbol)


if __name__ == "__main__":
    main(sys.argv[1:])
