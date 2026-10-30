"""Nasdaq.com cash index daily history -> bronze/nasdaq_index_daily.

NDX real level (the futures in multicharts_ohlcv are back-adjusted).
The API returns the whole ~10-year window every time: the Delta merge on
(symbol, timestamp) only adds the new days, so re-running is cheap and safe.

Run:
    .venv/bin/python applications/historical/nasdaq_index.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
from quantlake.bronze.connectors.nasdaq import NasdaqIndexDailyConnector
from symbols import CASH_INDICES

TABLE = NasdaqIndexDailyConnector.TABLE_NAME
connector = NasdaqIndexDailyConnector()
start = datetime(2015, 1, 1, tzinfo=timezone.utc)
now = datetime.now(timezone.utc)

for sym in CASH_INDICES:
    df = connector.fetch(symbol=sym, start=start, end=now)
    if df.is_empty():
        print(f"[{sym}] no data")
        continue
    df = bronze.add_partition_columns(df, symbol=sym)
    bronze.save(df, TABLE)
    print(f"[{sym}] {len(df):,} days, {df['timestamp'].min()} -> {df['timestamp'].max()}")
