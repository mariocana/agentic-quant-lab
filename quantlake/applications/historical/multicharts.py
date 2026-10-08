"""MultiCharts CSV exports -> bronze/multicharts_ohlcv.

Reads data/multicharts/<file>.csv written by the ExportBars indicator
(see the connector docstring) and merges the bars into bronze. Resumable:
only bars after the last stored timestamp are added. --full re-reads the
whole CSV and upserts every bar (after a connector change, or when the
back-adjusted continuous contract shifts history at a rollover).

Run:
    .venv/bin/python applications/historical/multicharts.py [--full]
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
from quantlake.bronze.connectors.multicharts import MultiChartsCSVConnector
from symbols import MC_FILES

TABLE = MultiChartsCSVConnector.TABLE_NAME
FULL = "--full" in sys.argv

for f in MC_FILES:
    connector = MultiChartsCSVConnector(chart_tz=f.chart_tz)
    if not (connector.folder / f"{f.file}.csv").exists():
        print(f"[{f.symbol}] {f.file}.csv not found in {connector.folder}")
        continue
    last = None if FULL else bronze.last_bronze_ts(TABLE, f.symbol)
    df = connector.fetch(symbol=f.file, start=last + timedelta(minutes=1) if last else None)
    if df.is_empty():
        print(f"[{f.symbol}] up to date")
        continue
    df = bronze.add_partition_columns(df, symbol=f.symbol)
    bronze.save(df, TABLE, update_matched=FULL)
    print(f"[{f.symbol}] {len(df):,} bars, {df['timestamp'].min()} -> {df['timestamp'].max()}")
