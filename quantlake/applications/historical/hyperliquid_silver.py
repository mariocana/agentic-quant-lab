"""Bronze Hyperliquid bars -> silver, with the underlying market's hours.

  silver/hyperliquid_ohlcv_1h, silver/hyperliquid_ohlcv_1d
      bronze columns + calendar, underlying_open_frac, underlying_market_open

Rebuilt in full every run: a change to the calendar map
(reference/hyperliquid_underlying.py) must reach every past bar, not only the
new ones. Run it after applications/historical/hyperliquid.py.

Run:
    poetry run python applications/historical/hyperliquid_silver.py
"""
import polars as pl
from deltalake import DeltaTable, write_deltalake

from quantlake.config import BRONZE_ROOT, REFERENCE_ROOT, SILVER_ROOT
from quantlake.silver.hyperliquid import add_underlying

listings = pl.from_arrow(DeltaTable(str(REFERENCE_ROOT / "hyperliquid_listings")).to_pyarrow_table(
    columns=["symbol", "dex"]))

for interval in ("1h", "1d"):
    src = str(BRONZE_ROOT / f"hyperliquid_ohlcv_{interval}")
    if not DeltaTable.is_deltatable(src):
        print(f"{interval}: no bronze table yet")
        continue
    bars = pl.from_arrow(DeltaTable(src).to_pyarrow_table())
    out = add_underlying(bars, listings, interval)
    write_deltalake(str(SILVER_ROOT / f"hyperliquid_ohlcv_{interval}"), out, mode="overwrite",
                    partition_by=["symbol", "year", "month"], schema_mode="overwrite")
    known = out.filter(pl.col("calendar").is_not_null())
    print(f"{interval}: {out.height:,} bars, {out['symbol'].n_unique()} perps; "
          f"underlying open on {known['underlying_market_open'].mean():.0%} of mapped bars, "
          f"{out['calendar'].null_count():,} bars unmapped")
