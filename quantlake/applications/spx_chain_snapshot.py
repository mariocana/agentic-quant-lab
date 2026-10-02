"""SPX option chain snapshot -> bronze/cboe_option_chain.

CBOE serves only the current (15-min delayed) chain: this script is how we
build our own option history, one snapshot per run. Scheduled with launchd
at fixed times (before London, before the US open, before the close).

Keeps expiries within 90 days and strikes within +-20% of spot.

Run:
    .venv/bin/python applications/spx_chain_snapshot.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import quantlake.bronze.ingest as bronze
from quantlake.bronze.connectors.cboe import CBOEOptionChainConnector
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
