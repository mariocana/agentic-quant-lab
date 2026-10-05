"""Build silver/cftc_cot + gold/cot_positioning/1w from bronze/cftc_cot.

Run AFTER the bronze ingester:

    historical/cftc_cot.py         -> bronze/cftc_cot
    historical/cot_positioning.py  -> silver/cftc_cot + gold/cot_positioning/1w (this script)

Weekly data is tiny (~2,000 rows per contract since 1986), so each run
rebuilds both tables from the full bronze history in one overwrite each:
rolling z-scores always see a complete window and re-running is safe.

Usage:
    .venv/bin/python applications/historical/cot_positioning.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from deltalake import DeltaTable

import quantlake.gold.cot as gold_cot
import quantlake.silver.cot as silver_cot
from quantlake.bronze.connectors.cftc_cot import CFTCCOTConnector
from quantlake.config import BRONZE_ROOT
from symbols import COT_INSTRUMENTS

BRONZE_PATH = str(BRONZE_ROOT / CFTCCOTConnector.TABLE_NAME)
if not DeltaTable.is_deltatable(BRONZE_PATH):
    sys.exit("bronze/cftc_cot missing - run historical/cftc_cot.py first")

meta = pl.DataFrame(
    {
        "symbol":   [i.symbol for i in COT_INSTRUMENTS],
        "category": [i.category for i in COT_INSTRUMENTS],
    }
)

bronze = pl.from_arrow(DeltaTable(BRONZE_PATH).to_pyarrow_table())
silver = silver_cot.rebuild(bronze)
gold = gold_cot.positioning(silver).join(meta, on="symbol", how="left")
gold_cot.save(gold)

last = gold.group_by("symbol").agg(pl.all().sort_by("timestamp").last())
by_symbol = {r["symbol"]: r for r in last.iter_rows(named=True)}
weeks = dict(gold.group_by("symbol").len().iter_rows())
for inst in COT_INSTRUMENTS:
    r = by_symbol.get(inst.symbol)
    if r is None:
        print(f"[{inst.symbol}] no bronze rows")
        continue
    z26 = "n/a" if r["z26"] is None else f"{r['z26']:+.2f}"
    print(f"[{inst.symbol}] {weeks[inst.symbol]:,} weeks, {r['report_date']} net {r['nc_net']:+,} z26 {z26}")
