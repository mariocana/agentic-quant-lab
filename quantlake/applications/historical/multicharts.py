"""MultiCharts CSV exports -> bronze/multicharts_ohlcv -> silver/multicharts_ohlcv.

Reads data/multicharts/<file>.csv written by the ExportBars indicator
(see the connector docstring) and merges the bars into bronze, then copies
into silver (clean_ohlcv) every bronze bar newer than the last silver one,
so an existing bronze is backfilled into silver on the first run.
Resumable: only new bars are added.

Gold is built by applications/historical/ohlcv_gold.py.

Run:
    .venv/bin/python applications/historical/multicharts.py
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
import quantlake.silver.ingest as silver
from quantlake.bronze.connectors.multicharts import MultiChartsCSVConnector
from quantlake.config import BRONZE_ROOT, SILVER_ROOT
from quantlake.storage import last_timestamp, read_symbol
from symbols import MC_FILES

TABLE = MultiChartsCSVConnector.TABLE_NAME


def sync_silver(symbol: str) -> None:
    last = last_timestamp(str(SILVER_ROOT / TABLE), symbol)
    since = last + timedelta(minutes=1) if last else None
    df = read_symbol(str(BRONZE_ROOT / TABLE), symbol, since=since)
    if df is None or df.is_empty():
        return
    silver.ingest(df.sort("timestamp"), TABLE)
    print(f"[{symbol}] silver +{len(df):,} bars")


def ingest_csv(f) -> None:
    connector = MultiChartsCSVConnector(chart_tz=f.chart_tz)
    if not (connector.folder / f"{f.file}.csv").exists():
        print(f"[{f.symbol}] {f.file}.csv not found in {connector.folder}")
        return
    last = bronze.last_bronze_ts(TABLE, f.symbol)
    df = connector.fetch(symbol=f.file, start=last + timedelta(minutes=1) if last else None)
    if df.is_empty():
        print(f"[{f.symbol}] bronze up to date")
        return
    df = bronze.add_partition_columns(df, symbol=f.symbol)
    bronze.save(df, TABLE)
    print(f"[{f.symbol}] bronze +{len(df):,} bars, {df['timestamp'].min()} -> {df['timestamp'].max()}")


for f in MC_FILES:
    ingest_csv(f)
    sync_silver(f.symbol)  # also when the CSV is missing: bronze may already hold bars
