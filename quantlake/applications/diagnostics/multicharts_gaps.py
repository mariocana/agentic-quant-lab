"""Are the holes in the MultiCharts 1m series minutes without trades, lost bars,
or a session template cutting the same window every day?

Read-only, fills nothing. Works on bronze/multicharts_ohlcv (raw export).
Rules and columns: quantlake.silver.gaps.

  recurring windows   same time-of-day window missing in > 50% of a month's
                      trading days → session template, not missing data
  early Fridays       months where most Fridays end before 15:59 CT
  per hole            Chicago hour, RTH vs overnight, neighbours' volume vs
                      the same hour/year median (rel_vol < 1 = thinner),
                      |open after - close before| in ticks

Minutes without trades: overnight, thin neighbours, price unchanged (0-1
tick). Lost bars: RTH or busy neighbours and price jumps across the hole.

Run:
    .venv/bin/python applications/diagnostics/multicharts_gaps.py            # ES
    .venv/bin/python applications/diagnostics/multicharts_gaps.py NQ
"""
import sys

import polars as pl

from quantlake.config import BRONZE_ROOT
from quantlake.silver.gaps import early_fridays, find_gaps, recurring_gaps, summarize
from quantlake.storage import read_symbol

TABLE = "multicharts_ohlcv"


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "ES"
    bars = read_symbol(str(BRONZE_ROOT / TABLE), symbol)
    if bars is None or bars.is_empty():
        raise SystemExit(f"no bronze/{TABLE} rows for {symbol}")
    gaps = find_gaps(bars)
    print(f"{symbol}: {gaps.height:,} gaps, {gaps['missing'].sum():,} missing minutes (1-59 min, halt excluded)")
    tables = {
        "recurring windows (session template?)": recurring_gaps(bars),
        "months with Fridays ending before 15:59 CT": early_fridays(bars),
        **summarize(gaps),
    }
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=200):
        for name, df in tables.items():
            print(f"\n── {name}" + (": none" if df.is_empty() else ""))
            if not df.is_empty():
                print(df)


if __name__ == "__main__":
    main()
