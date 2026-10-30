"""Silver for Sentinel-2 crop NDVI: anomaly vs prior seasons.

bronze/sentinel2_ndvi -> silver/sentinel2_ndvi_anomaly

The 03 notebook in pipeline form, with one change: the baseline for a
season is the mean of the seasons BEFORE it, never including itself or
later ones. A backtest that reads the 2023 anomaly then only sees what
was known in 2023.

Per AOI (symbol):
  1. keep dates with valid_frac >= MIN_VALID_FRAC (cloudy over the AOI
     even when the scene passed the 30% cloud filter)
  2. each prior season is interpolated onto a daily day-of-season grid
     (safe: a prior season is complete before the current one starts)
  3. for each observation of the current season, at its doy_season:
       baseline_mean / baseline_std over prior seasons,
       anomaly = ndvi_mean - baseline_mean, anomaly_z = anomaly / std
     The current season itself is never interpolated: interpolating
     between today's and next week's image would use the future.

Rebuilt in full on every run (tiny table) and written in one overwrite,
partitioned by symbol, like the COT silver.
"""
import numpy as np
import polars as pl
from deltalake import write_deltalake

from quantlake.config import SILVER_ROOT

TABLE = "sentinel2_ndvi_anomaly"
MIN_VALID_FRAC = 0.5
_GRID = np.arange(0, 366)


def anomaly(bronze: pl.DataFrame, min_valid_frac: float = MIN_VALID_FRAC) -> pl.DataFrame:
    df = (
        bronze.filter(pl.col("valid_frac") >= min_valid_frac)
        .unique(subset=["symbol", "acq_date"], keep="last")
        .sort(["symbol", "season", "doy_season"])
    )
    out = []
    for _, g in df.group_by("symbol", maintain_order=True):
        curves = {
            season: _interp(s["doy_season"].to_numpy(), s["ndvi_mean"].to_numpy())
            for (season,), s in g.group_by("season", maintain_order=True)
        }
        means, stds, counts = [], [], []
        for season, doy in zip(g["season"].to_list(), g["doy_season"].to_list()):
            prior = np.array([curves[p][doy] for p in curves if p < season])
            prior = prior[~np.isnan(prior)]
            means.append(prior.mean() if len(prior) else None)
            stds.append(prior.std(ddof=1) if len(prior) >= 2 else None)
            counts.append(len(prior))
        out.append(g.with_columns(
            pl.Series("baseline_mean", means, dtype=pl.Float64),
            pl.Series("baseline_std", stds, dtype=pl.Float64),
            pl.Series("n_baseline", counts, dtype=pl.Int32),
        ))
    if not out:
        return df
    return pl.concat(out).with_columns(
        (pl.col("ndvi_mean") - pl.col("baseline_mean")).alias("anomaly"),
    ).with_columns(
        pl.when(pl.col("baseline_std") > 0)
        .then(pl.col("anomaly") / pl.col("baseline_std"))
        .alias("anomaly_z"),
    )


def rebuild(bronze: pl.DataFrame) -> pl.DataFrame:
    df = anomaly(bronze)
    if not df.is_empty():
        write_deltalake(str(SILVER_ROOT / TABLE), df.to_arrow(), mode="overwrite",
                        partition_by=["symbol"], schema_mode="overwrite")
    return df


def _interp(doy: np.ndarray, ndvi: np.ndarray) -> np.ndarray:
    if len(doy) < 2:
        return np.full(len(_GRID), np.nan)
    return np.interp(_GRID, doy, ndvi, left=np.nan, right=np.nan)
