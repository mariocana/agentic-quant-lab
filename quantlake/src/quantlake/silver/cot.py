"""Silver for CFTC Commitments of Traders (bronze/cftc_cot -> silver/cftc_cot).

Row-wise only: everything here depends on a single weekly report.
Cross-week metrics (changes, z-scores) live in gold/cot_positioning.

Unlike the OHLCV silvers this table is not merged: it is rebuilt in full
from bronze on every run (a few tens of thousands of rows) and written in
one overwrite, partitioned by symbol only. Per-symbol merges on
[symbol, year, month] meant ~4 rows per file and minutes per rebuild.

  - drop reports missing open interest or non-commercial long/short
  - dedupe on (symbol, report_date)
  - net positions per trader group, and non-commercial net as % of OI
    (null when OI <= 0)
"""
import polars as pl
from deltalake import write_deltalake

from quantlake.config import SILVER_ROOT

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


def rebuild(bronze: pl.DataFrame) -> pl.DataFrame:
    """Clean the full bronze history and overwrite silver/cftc_cot."""
    if bronze.is_empty():
        return bronze
    df = clean_cot(bronze)
    write_deltalake(str(SILVER_ROOT / TABLE), df.to_arrow(), mode="overwrite",
                    partition_by=["symbol"], schema_mode="overwrite")
    return df
