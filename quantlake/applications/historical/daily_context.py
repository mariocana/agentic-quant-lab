"""Build gold/daily_context/1d (Stucchi playbook context) for ES and NQ.

Inputs (run their loaders first):
    silver/multicharts_ohlcv   historical/multicharts.py
    bronze/cboe_index_daily    historical/cboe_vix.py
    bronze/squeezemetrics      historical/squeezemetrics.py
    bronze/nasdaq_index_daily  historical/nasdaq_index.py

Full rebuild every run (~2,700 days x 2 symbols). Prints the latest row
per symbol: run in the morning, it is today's pre-London context.

Run:
    .venv/bin/python applications/historical/daily_context.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from deltalake import DeltaTable

import quantlake.gold.context as context
from quantlake.config import BRONZE_ROOT, SILVER_ROOT
from quantlake.storage import read_symbol


def _bronze(table: str) -> pl.DataFrame:
    path = str(BRONZE_ROOT / table)
    if not DeltaTable.is_deltatable(path):
        sys.exit(f"bronze/{table} missing - run its loader first")
    return pl.from_arrow(DeltaTable(path).to_pyarrow_table())


sources = context.daily_sources(
    _bronze("cboe_index_daily"), _bronze("squeezemetrics"), _bronze("nasdaq_index_daily")
)
cols = ["timestamp", "open", "high", "low", "close", "volume", "upticks", "downticks"]
frames = []
for symbol in context.SYMBOLS:
    bars = read_symbol(str(SILVER_ROOT / "multicharts_ohlcv"), symbol, columns=cols)
    if bars is None or bars.is_empty():
        print(f"[{symbol}] no silver bars - run historical/multicharts.py")
        continue
    frames.append(context.build(symbol, bars, sources))

df = pl.concat(frames)
context.save(df)

for r in df.group_by("symbol").agg(pl.all().sort_by("date").last()).sort("symbol").iter_rows(named=True):
    def f(x, d=1):
        return "-" if x is None else f"{x:,.{d}f}"
    print(
        f"[{r['symbol']}] {df.filter(pl.col('symbol') == r['symbol']).height:,} days, last {r['date']}: "
        f"EM {f(r['em'])} pt (IV {f(r['iv'])}, pct {f(r['iv_pct'], 2)}), "
        f"GEX {r['gex_regime']} pct {f(r['gex_pct'], 2)}, {r['quadrant']}, "
        f"prev H/L/C {f(r['prev_high'], 2)}/{f(r['prev_low'], 2)}/{f(r['prev_close'], 2)}"
    )
