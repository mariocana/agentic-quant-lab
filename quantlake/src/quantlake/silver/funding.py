"""silver/binance_um_funding: one row per (symbol, funding settlement).

Columns: timestamp (UTC), symbol, funding_rate, ingested_at, year, month.
mark_price stays in bronze.

  - timestamp is truncated to the second: Binance publishes fundingTime a
    few ms past the settlement (e.g. 00:00:00.008), the settlement is 00:00:00.
  - funding_rate inf / null -> NaN (never dropped, like clean_ohlcv).
  - duplicates on (symbol, timestamp) keep the most recently ingested row.
"""
import polars as pl

import quantlake.silver.ingest as silver

FUNDING = "binance_um_funding"

SCHEMA = {
    "timestamp":    pl.Datetime("us", "UTC"),
    "symbol":       pl.String,
    "funding_rate": pl.Float64,
    "ingested_at":  pl.Datetime("us", "UTC"),
    "year":         pl.Int32,
    "month":        pl.Int8,
}


def clean_funding(df: pl.DataFrame) -> pl.DataFrame:
    """Bronze funding rows (with symbol/year/month/ingested_at) -> silver schema."""
    if df.is_empty():
        return pl.DataFrame(schema=SCHEMA)
    rate = pl.col("funding_rate").cast(pl.Float64)
    return (
        df.with_columns(
            pl.col("timestamp").dt.truncate("1s"),
            pl.when(rate.is_infinite() | rate.is_null()).then(float("nan")).otherwise(rate).alias("funding_rate"),
        )
        .with_columns(
            pl.col("timestamp").dt.year().cast(pl.Int32).alias("year"),
            pl.col("timestamp").dt.month().cast(pl.Int8).alias("month"),
        )
        .sort("ingested_at")
        .unique(subset=["symbol", "timestamp"], keep="last")
        .select([pl.col(c).cast(t) for c, t in SCHEMA.items()])
        .sort("symbol", "timestamp")
    )


def save_funding(df: pl.DataFrame) -> pl.DataFrame:
    clean = clean_funding(df)
    silver.save(clean, FUNDING)
    return clean
