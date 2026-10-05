"""CFTC Commitments of Traders (legacy, futures only) -> bronze/cftc_cot.

Migrated from the cot-analyzer project (Postgres cot_weekly table).
Resumes per symbol from last_bronze_ts; first run pulls the full history
since 1986.

Storage differs from the other bronze tables on purpose: plain Delta
append, partitioned by symbol only. With [symbol, year, month] a weekly
table means ~15k files of ~4 rows, and each merge rescans all of them
(measured: >10 min for one weekly update). Append stays idempotent
because the connector only returns reports strictly after
last_bronze_ts; silver dedupes on (symbol, report_date) anyway.

Run:
    .venv/bin/python applications/historical/cftc_cot.py              # all
    .venv/bin/python applications/historical/cftc_cot.py EUR GC       # some
"""
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from deltalake import write_deltalake

import quantlake.bronze.ingest as bronze
from quantlake.bronze.connectors.cftc_cot import CFTCCOTConnector
from quantlake.config import BRONZE_ROOT
from symbols import COT_INSTRUMENTS

from dotenv import load_dotenv

load_dotenv()


COT_START = datetime(1986, 1, 1, tzinfo=timezone.utc)
TABLE = CFTCCOTConnector.TABLE_NAME

wanted = set(sys.argv[1:])
unknown = wanted - {i.symbol for i in COT_INSTRUMENTS}
if unknown:
    sys.exit(f"unknown symbols: {', '.join(sorted(unknown))}")

connector = CFTCCOTConnector()
now = datetime.now(timezone.utc)
errors = []

for inst in COT_INSTRUMENTS:
    if wanted and inst.symbol not in wanted:
        continue
    last = bronze.last_bronze_ts(TABLE, inst.symbol)
    start = last + timedelta(seconds=1) if last else COT_START
    try:
        df = connector.fetch(symbol=inst.cftc_code, start=start, end=now)
    except Exception as e:
        errors.append(inst.symbol)
        print(f"[{inst.symbol}] ERROR {e}")
        continue
    if df.is_empty():
        print(f"[{inst.symbol}] up to date")
    else:
        df = bronze.add_partition_columns(df, symbol=inst.symbol)
        write_deltalake(str(BRONZE_ROOT / TABLE), df.to_arrow(), mode="append", partition_by=["symbol"])
        print(f"[{inst.symbol}] {len(df):,} weeks, last report {df['report_date'].max()}")
    time.sleep(connector.pause_s)  # be polite with Socrata

if errors:
    sys.exit(f"failed: {', '.join(errors)}")
