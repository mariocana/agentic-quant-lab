"""Silver for CFTC Commitments of Traders (bronze/cftc_cot -> silver/cftc_cot).

Row-wise only: everything here depends on a single weekly report, so a
silver row never changes once written. Cross-week metrics (changes,
z-scores) live in gold/cot_positioning.

  - drop reports missing open interest or non-commercial long/short
  - dedupe on (symbol, report_date)
  - net positions per trader group, and non-commercial net as % of OI
    (null when OI <= 0)
"""
import polars as pl

import quantlake.silver.ingest as silver

TABLE = "cftc_cot"


def clean_cot(df: pl.DataFrame) -> pl.DataFrame:
    """Clean a bronze cftc_cot frame (with partition columns) and add net columns."""
    return (
        df.drop_nulls(["open_interest", "nc_long", "nc_short"])
        .unique(subset=["symbol", "report_date"], keep="last")
        .with_columns(
            (pl.col("nc_long") - pl.col("nc_short")).alias("nc_net"),
            (pl.col("comm_long") - pl.col("comm_short")).alias("comm_net"),
            (pl.col("nonrept_long") - pl.col("nonrept_short")).alias("nonrept_net"),
        )
        .with_columns(
            pl.when(pl.col("open_interest") > 0)
            .then(100 * pl.col("nc_net") / pl.col("open_interest"))
            .otherwise(None)
            .alias("nc_net_pct_oi"),
        )
        .sort(["symbol", "timestamp"])
    )


def ingest(df: pl.DataFrame) -> pl.DataFrame:
    """Clean and persist to silver/cftc_cot. Insert-only, safe to re-run."""
    if df.is_empty():
        return df
    df = clean_cot(df)
    silver.save(df, TABLE)
    return df
