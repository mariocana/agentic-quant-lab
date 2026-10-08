"""Are the holes in the MultiCharts 1m series minutes without trades, or lost bars?

Read-only, fills nothing. Works on bronze/multicharts_ohlcv (raw export).

A gap = consecutive bars more than 1 minute apart, 1-59 minutes missing,
not overlapping the 16:00-17:00 Chicago halt (longer gaps are weekends,
holidays, halts). MultiCharts builds a bar only when a tick arrives, so a
minute without trades has no bar. For each gap it measures:

  - Chicago hour and RTH (08:30-15:15 CT) vs overnight,
  - volume / ticks of the bar before and after vs the median of bars in
    the same Chicago hour of the same year (rel_volume < 1 = thinner),
  - |open after - close before| in ticks.

Minutes without trades: overnight, thin neighbours (rel_volume well below
1, few ticks) and price unchanged (0-1 tick). Lost bars: RTH or busy
neighbours, and price jumps of several ticks across the hole.

Run:
    .venv/bin/python applications/diagnostics/multicharts_gaps.py            # ES
    .venv/bin/python applications/diagnostics/multicharts_gaps.py NQ
"""
import sys
from datetime import time

import polars as pl

from quantlake.config import BRONZE_ROOT
from quantlake.storage import read_symbol

TABLE = "multicharts_ohlcv"
TZ = "America/Chicago"
TICK = 0.25
RTH = (time(8, 30), time(15, 15))
HALT = (time(16, 0), time(17, 0))


def find_gaps(bars: pl.DataFrame, tick: float = TICK) -> pl.DataFrame:
    """One row per gap with its context (see module docstring)."""
    b = bars.sort("timestamp")
    vol = "volume" if "volume" in b.columns else None
    local = pl.col("timestamp").dt.convert_time_zone(TZ)
    b = b.with_columns(
        local.dt.year().alias("year"),
        local.dt.hour().alias("hour"),
        *([pl.col("ticks")] if "ticks" in b.columns else [pl.lit(None, dtype=pl.Float64).alias("ticks")]),
        *([pl.col(vol).alias("vol")] if vol else [pl.lit(None, dtype=pl.Float64).alias("vol")]),
    )
    hourly = b.group_by("year", "hour").agg(pl.col("vol").median().alias("med_vol"),
                                            pl.col("ticks").median().alias("med_ticks"))
    b = b.join(hourly, on=["year", "hour"], how="left").with_columns(
        (pl.col("vol") / pl.col("med_vol")).alias("rel_vol"),
        (pl.col("ticks") / pl.col("med_ticks")).alias("rel_ticks"),
    )
    nxt = b.shift(-1)
    gaps = pl.DataFrame({
        "before": b["timestamp"], "after": nxt["timestamp"],
        "year": b["year"], "close_before": b["close"], "open_after": nxt["open"],
        "rel_vol_before": b["rel_vol"], "rel_vol_after": nxt["rel_vol"],
        "ticks_before": b["ticks"], "ticks_after": nxt["ticks"],
    }).with_columns(
        ((pl.col("after") - pl.col("before")).dt.total_minutes() - 1).alias("missing"),
        (pl.col("before") + pl.duration(minutes=1)).dt.convert_time_zone(TZ).alias("first_missing_ct"),
        (pl.col("after") - pl.duration(minutes=1)).dt.convert_time_zone(TZ).alias("last_missing_ct"),
        ((pl.col("open_after") - pl.col("close_before")).abs() / tick).round(2).alias("jump_ticks"),
    ).filter(pl.col("missing").is_between(1, 59))
    first_t, last_t = pl.col("first_missing_ct").dt.time(), pl.col("last_missing_ct").dt.time()
    in_halt = (last_t >= HALT[0]) & (first_t < HALT[1])
    return gaps.filter(~in_halt).with_columns(
        pl.col("first_missing_ct").dt.hour().alias("hour_ct"),
        ((first_t >= RTH[0]) & (first_t < RTH[1])).alias("rth"),
    )


def summarize(gaps: pl.DataFrame) -> dict[str, pl.DataFrame]:
    by_year = gaps.group_by("year").agg(
        pl.len().alias("gaps"),
        pl.col("missing").sum().alias("missing_min"),
        (pl.col("missing") == 1).sum().alias("len_1"),
        pl.col("missing").is_between(2, 5).sum().alias("len_2_5"),
        (pl.col("missing") > 5).sum().alias("len_6_59"),
        pl.col("rth").mean().round(3).alias("share_rth"),
        pl.col("rel_vol_before").median().round(3).alias("med_rel_vol_before"),
        pl.col("rel_vol_after").median().round(3).alias("med_rel_vol_after"),
        pl.col("ticks_before").median().alias("med_ticks_before"),
        pl.col("jump_ticks").median().alias("med_jump_ticks"),
        (pl.col("jump_ticks") <= 1).mean().round(3).alias("share_jump_le_1"),
    ).sort("year")
    by_hour = gaps.group_by("hour_ct").agg(pl.len().alias("gaps"), pl.col("missing").sum().alias("missing_min")).sort("hour_ct")
    suspicious = gaps.filter(pl.col("rth") & (pl.col("jump_ticks") >= 4)).sort("jump_ticks", descending=True).head(20)
    return {"by_year": by_year, "by_hour_ct": by_hour, "rth_with_jumps": suspicious}


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "ES"
    bars = read_symbol(str(BRONZE_ROOT / TABLE), symbol)
    if bars is None or bars.is_empty():
        raise SystemExit(f"no bronze/{TABLE} rows for {symbol}")
    gaps = find_gaps(bars)
    print(f"{symbol}: {gaps.height:,} gaps, {gaps['missing'].sum():,} missing minutes (1-59 min, halt excluded)")
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=200):
        for name, df in summarize(gaps).items():
            print(f"\n── {name}")
            print(df)


if __name__ == "__main__":
    main()
