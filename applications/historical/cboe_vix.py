"""CBOE volatility indices daily history -> bronze/cboe_index_daily.

VIX (1990-), VIX9D (2011-), VIX1D (2022-), VIX3M (2006-), VXN (2009-). The CSV is the
full history every time: the Delta merge on (symbol, timestamp) only adds
the new days, so re-running is cheap and safe.

Run:
    .venv/bin/python applications/historical/cboe_vix.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
from quantlake.bronze.connectors.cboe import CBOEIndexDailyConnector
from symbols import VOL_INDICES

TABLE = CBOEIndexDailyConnector.TABLE_NAME
connector = CBOEIndexDailyConnector()
start = datetime(1990, 1, 1, tzinfo=timezone.utc)
now = datetime.now(timezone.utc)

for sym in VOL_INDICES:
    df = connector.fetch(symbol=sym, start=start, end=now)
    if df.is_empty():
        print(f"[{sym}] no data")
        continue
    df = bronze.add_partition_columns(df, symbol=sym)
    bronze.save(df, TABLE)
    print(f"[{sym}] {len(df):,} days, last {df['timestamp'].max()}")
