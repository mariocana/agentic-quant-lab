"""Gold for CFTC Commitments of Traders (silver/cftc_cot -> gold/cot_positioning/1w).

Weekly positioning context per contract, ported from cot-analyzer's
core.build_snapshots so the web app can read rows instead of recomputing:

  - week-over-week changes: nc_long_chg, nc_short_chg, nc_net_chg
  - z26 / pct_rank_26 and z52 / pct_rank_52 of nc_net

Z-scores compare each week against the PRIOR weeks only (the current
report is excluded from its own window), as in cot-analyzer. With fewer
weeks than the lookback, all available prior weeks are used, but at
least MIN_WEEKS; below that, or with zero dispersion, the value is null.
pct_rank = % of prior weeks in the window with nc_net strictly below the
current one.

Rows keep the release `timestamp` from bronze, so an as-of join onto
price bars only sees a report after it was published.
"""
import numpy as np
import polars as pl
from deltalake import write_deltalake

from quantlake.config import GOLD_ROOT

TABLE = "cot_positioning"
TIMEFRAME = "1w"
LOOKBACKS = (26, 52)
MIN_WEEKS = 10


def positioning(df: pl.DataFrame) -> pl.DataFrame:
    """Build gold rows from a silver cftc_cot frame (any number of symbols)."""
    if df.is_empty():
        return df
    out = []
    for _, g in df.sort(["symbol", "timestamp"]).group_by("symbol", maintain_order=True):
        g = g.with_columns(
            pl.col("nc_long").diff().alias("nc_long_chg"),
            pl.col("nc_short").diff().alias("nc_short_chg"),
            pl.col("nc_net").diff().alias("nc_net_chg"),
        )
        net = g["nc_net"].cast(pl.Float64).to_numpy()
        for lb in LOOKBACKS:
            z, rank = _prior_window_stats(net, lb)
            g = g.with_columns(
                pl.Series(f"z{lb}", z, dtype=pl.Float64),
                pl.Series(f"pct_rank_{lb}", rank, dtype=pl.Float64),
            )
        out.append(g)
    return pl.concat(out).with_columns(pl.col(pl.Float64).fill_nan(None))


def save(df: pl.DataFrame) -> None:
    """Overwrite gold/cot_positioning/1w (full rebuild, partitioned by symbol).

    Same reasoning as silver/cot.rebuild: the whole table is recomputed from
    silver every run, so one overwrite replaces 32 per-symbol merges.
    """
    if df.is_empty():
        return
    write_deltalake(str(GOLD_ROOT / TABLE / TIMEFRAME), df.to_arrow(), mode="overwrite",
                    partition_by=["symbol"], schema_mode="overwrite")


def _prior_window_stats(x: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    z = np.full(len(x), np.nan)
    rank = np.full(len(x), np.nan)
    for i in range(MIN_WEEKS, len(x)):
        past = x[max(0, i - lookback):i]
        std = past.std(ddof=1)
        if std == 0 or np.isnan(std):
            continue
        z[i] = (x[i] - past.mean()) / std
        rank[i] = 100 * np.count_nonzero(past < x[i]) / len(past)
    return z, rank
