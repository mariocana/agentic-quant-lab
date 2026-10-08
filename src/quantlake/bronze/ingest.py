from datetime import datetime, timezone
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.config import BRONZE_ROOT
from quantlake.storage import last_timestamp, upsert


def last_bronze_ts(table_name: str, symbol: str) -> datetime | None:
    """Return the latest timestamp already ingested for (table, symbol), or None.

    Used to make historical scripts resumable: callers pull only from
    `last_bronze_ts(...) + 1 unit` onward instead of re-downloading everything.
    """
    return last_timestamp(str(BRONZE_ROOT / table_name), symbol)


def ingest(connector: HistoricalConnector, symbol, start, end):
    df = connector.fetch(symbol=symbol, start=start, end=end)
    if df.is_empty():
        return df
    df = add_partition_columns(df, symbol)
    save(df, connector.TABLE_NAME)
    return df


def save(df, table_name, update_matched=False):
    upsert(df, str(BRONZE_ROOT / table_name), update_matched=update_matched)


def add_partition_columns(df, symbol):
    df = df.with_columns(
        pl.lit(symbol).alias("symbol"),
        pl.col("timestamp").dt.year().cast(pl.Int32).alias("year"),
        pl.col("timestamp").dt.month().cast(pl.Int8).alias("month"),
    )
    if "ingested_at" not in df.columns:
        df = df.with_columns(
            pl.lit(datetime.now(timezone.utc)).cast(pl.Datetime("us", "UTC")).alias("ingested_at")
        )
    return df