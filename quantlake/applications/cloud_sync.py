"""Import the SPX chain snapshots taken in the cloud (R2) into bronze/cboe_option_chain.

The Railway job (cloud/chain_job.py) writes one parquet per snapshot; here every
file whose timestamp is not yet in bronze is merged, then gold/em_0dte is
rebuilt. Without R2_* in .env it does nothing (exit 0), so contesto.py can
always call it.

Run:
    .venv/bin/python applications/cloud_sync.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import polars as pl
from deltalake import DeltaTable

import quantlake.bronze.ingest as bronze
import quantlake.gold.options as options
from quantlake import remote
from quantlake.bronze.connectors.cboe import CBOEOptionChainConnector
from quantlake.config import BRONZE_ROOT

PREFIX = "cboe_option_chain/SPX"
TABLE = CBOEOptionChainConnector.TABLE_NAME
PATH = str(BRONZE_ROOT / TABLE)

if remote.store() is None:
    print("R2 not configured (R2_* in .env): nothing to import")
    sys.exit(0)

have = set()
if DeltaTable.is_deltatable(PATH):
    have = set(pl.from_arrow(DeltaTable(PATH).to_pyarrow_table(columns=["timestamp"]))["timestamp"].unique())

added = 0
for key in remote.list_keys(PREFIX):
    df = remote.read_parquet(key)
    if df.is_empty() or df["timestamp"][0] in have:
        continue
    bronze.save(bronze.add_partition_columns(df, symbol="SPX"), TABLE)
    have.add(df["timestamp"][0])
    added += 1
    print(f"[SPX] imported {key} ({len(df):,} options)")

if added:
    options.save(options.build(pl.from_arrow(DeltaTable(PATH).to_pyarrow_table())))
print(f"[SPX] {added} new snapshot(s) from R2")
