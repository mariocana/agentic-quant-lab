"""SPX option chain snapshot -> bronze/cboe_option_chain.

CBOE serves only the current (15-min delayed) chain: this script is how we
build our own option history, one snapshot per run. Scheduled with launchd
at fixed times (before London, before the US open, before the close).

Keeps expiries within 90 days and strikes within +-20% of spot. After the
save, gold/em_0dte (0DTE ATM straddle per snapshot) is rebuilt.

Run:
    .venv/bin/python applications/spx_chain_snapshot.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import polars as pl
from deltalake import DeltaTable

import quantlake.bronze.ingest as bronze
import quantlake.gold.options as options
from quantlake.bronze.connectors.cboe import CBOEOptionChainConnector
from quantlake.config import BRONZE_ROOT
from symbols import CHAIN_UNDERLYINGS

TABLE = CBOEOptionChainConnector.TABLE_NAME
connector = CBOEOptionChainConnector(max_dte=90, strike_band=0.20)

for sym in CHAIN_UNDERLYINGS:
    df = connector.fetch(symbol=sym)
    if df.is_empty():
        print(f"[{sym}] empty chain")
        continue
    df = bronze.add_partition_columns(df, symbol=sym)
    bronze.save(df, TABLE)
    print(f"[{sym}] {len(df):,} options, spot {df['spot'][0]}, at {df['timestamp'][0]}")

em = options.build(pl.from_arrow(DeltaTable(str(BRONZE_ROOT / TABLE)).to_pyarrow_table()))
options.save(em)
if not em.is_empty():
    r = em.row(-1, named=True)
    print(f"[EM 0DTE] {r['expiry']}: straddle {r['straddle']:.1f} pt ({r['em_pct']:.2%}), forward {r['forward']:.1f}, "
          f"{r['minutes_to_close']:.0f} min to close")
