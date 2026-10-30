"""0DTE expected move from SPX chain snapshots -> gold/em_0dte/snapshot.

One row per snapshot in bronze/cboe_option_chain that has an SPXW expiry on
the same US Eastern date (0DTE). The expected move is the ATM straddle:

    forward    put-call parity on the strike where |call - put| is smallest:
               F = K + C - P (mid prices). Before the cash open the chain's
               `spot` is still yesterday's close, the forward is not.
    straddle   call + put mid at F, linearly interpolated between the two
               strikes around F
    em_pct     straddle / forward

The straddle shrinks during the day (less time left): the row of the last
snapshot before 09:30 ET is the one comparable with Stucchi's EM at the open
(gold/daily_context em_stucchi = 0.7 x VIX1D-open sigma).
"""
from zoneinfo import ZoneInfo

import polars as pl
from deltalake import write_deltalake

from quantlake.config import GOLD_ROOT

TABLE = "em_0dte"
TIMEFRAME = "snapshot"
ET = "America/New_York"


def _one(snap: pl.DataFrame) -> dict | None:
    ts = snap["timestamp"][0]
    day = ts.astimezone(ZoneInfo(ET)).date()
    z = snap.filter((pl.col("root") == "SPXW") & (pl.col("expiry") == day) & (pl.col("bid") > 0) & (pl.col("ask") > 0))
    if z.is_empty():
        return None
    mid = z.with_columns(((pl.col("bid") + pl.col("ask")) / 2).alias("mid"))
    pairs = (
        mid.filter(pl.col("right") == "C").select("strike", pl.col("mid").alias("c"), pl.col("iv").alias("iv_c"))
        .join(mid.filter(pl.col("right") == "P").select("strike", pl.col("mid").alias("p"), pl.col("iv").alias("iv_p")), on="strike")
        .sort("strike")
    )
    if pairs.height < 2:
        return None
    k0 = pairs.with_columns((pl.col("c") - pl.col("p")).abs().alias("d")).sort("d").row(0, named=True)
    fwd = k0["strike"] + k0["c"] - k0["p"]
    below = pairs.filter(pl.col("strike") <= fwd).tail(1)
    above = pairs.filter(pl.col("strike") > fwd).head(1)
    if below.is_empty() or above.is_empty():
        return None
    k1, s1 = below["strike"][0], below["c"][0] + below["p"][0]
    k2, s2 = above["strike"][0], above["c"][0] + above["p"][0]
    straddle = s1 + (s2 - s1) * (fwd - k1) / (k2 - k1)
    close = ts.astimezone(ZoneInfo(ET)).replace(hour=16, minute=0, second=0, microsecond=0)
    return {
        "timestamp": ts,
        "symbol": snap["symbol"][0],
        "expiry": day,
        "spot": snap["spot"][0],
        "forward": fwd,
        "atm_strike": k0["strike"],
        "straddle": straddle,
        "em_pct": straddle / fwd,
        "iv_atm": (k0["iv_c"] + k0["iv_p"]) / 2,
        "minutes_to_close": max((close - ts.astimezone(close.tzinfo)).total_seconds() / 60, 0),
    }


def build(chain: pl.DataFrame) -> pl.DataFrame:
    rows = [r for (_,), snap in chain.group_by("timestamp") if (r := _one(snap)) is not None]
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).with_columns(
        pl.col("timestamp").cast(pl.Datetime("us", "UTC")),
        pl.col("timestamp").dt.convert_time_zone(ET).dt.time().lt(pl.time(9, 30)).alias("pre_open"),
    ).sort("timestamp")


def save(df: pl.DataFrame) -> None:
    """Overwrite gold/em_0dte/snapshot (tiny: one row per snapshot)."""
    if df.is_empty():
        return
    write_deltalake(str(GOLD_ROOT / TABLE / TIMEFRAME), df.to_arrow(), mode="overwrite", schema_mode="overwrite")
