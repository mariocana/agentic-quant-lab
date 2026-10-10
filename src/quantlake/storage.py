"""Shared Delta IO for the bronze / silver / gold time-series tables.

  upsert        idempotent write: first write creates the table, then merge
  read_symbol   one symbol's rows, partition-pruned, optional since / until
  symbols       distinct symbols (from the Delta log, no data scan)
  first_timestamp / last_timestamp, delete_range / delete_symbol

Three things matter here.

1. Partition columns are (symbol, year, month). Filtering on any of
   these prunes entire subdirectories.

2. The merge predicate matches on (symbol, timestamp). Re-running an
   ingest with the same range never duplicates a row.

3. The first write creates the table; subsequent writes merge.
"""

from datetime import datetime

import polars as pl
from deltalake import DeltaTable, write_deltalake

PARTITION_BY = ["symbol", "year", "month"]
MERGE_PREDICATE = ("s.timestamp = t.timestamp AND s.symbol = t.symbol AND s.year = t.year AND s.month = t.month")


def upsert(df: pl.DataFrame, table_path: str, update_matched: bool = False) -> None:
    """Merge df into the Delta table at table_path, or create it on first write.

    update_matched=True lets gold overwrite partial bars saved by a prior batch run
    (useful when the live stream completes a TF bar that batch had saved early).
    """
    if DeltaTable.is_deltatable(table_path):
        merge = (
            DeltaTable(table_path)
            .merge(df.to_arrow(), predicate=MERGE_PREDICATE, source_alias="s", target_alias="t")
            .when_not_matched_insert_all()
        )
        if update_matched:
            merge = merge.when_matched_update_all()
        merge.execute()
    else:
        write_deltalake(table_path, df, mode="overwrite", partition_by=PARTITION_BY)


def read_symbol(
    table_path: str,
    symbol: str,
    columns: list[str] | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> pl.DataFrame | None:
    """Read one symbol's rows (partition-pruned), or None if the table doesn't exist.

    ``since`` keeps rows with timestamp >= since, ``until`` rows with
    timestamp < until. Both prune the year partitions outside the range and
    are pushed down on timestamp, so Parquet row-group statistics skip the
    rest (reading the head before a recent first bar stays cheap).
    """
    if not DeltaTable.is_deltatable(table_path):
        return None
    filters = [("symbol", "=", symbol)]
    if since is not None:
        filters += [("year", ">=", since.year), ("timestamp", ">=", since)]
    if until is not None:
        filters += [("year", "<=", until.year), ("timestamp", "<", until)]
    df = pl.from_arrow(DeltaTable(table_path).to_pyarrow_table(columns=columns, filters=filters))
    if since is not None:
        df = df.filter(pl.col("timestamp") >= since)
    if until is not None:
        df = df.filter(pl.col("timestamp") < until)
    return df


def symbols(table_path: str) -> list[str]:
    """Distinct symbols of a table partitioned by symbol (read from the Delta log, no data scan)."""
    if not DeltaTable.is_deltatable(table_path):
        return []
    return sorted({p["symbol"] for p in DeltaTable(table_path).partitions()})


def first_timestamp(table_path: str, symbol: str) -> datetime | None:
    """Earliest timestamp stored for symbol, or None if the table or symbol is missing."""
    df = read_symbol(table_path, symbol, columns=["timestamp"])
    if df is None or df.is_empty():
        return None
    return df["timestamp"].min()


def last_timestamp(table_path: str, symbol: str) -> datetime | None:
    """Latest timestamp stored for symbol, or None if the table or symbol is missing."""
    df = read_symbol(table_path, symbol, columns=["timestamp"])
    if df is None or df.is_empty():
        return None
    return df["timestamp"].max()



def delete_range(table_path: str, symbol: str, start: datetime, end: datetime) -> int:
    """Delete symbol's rows with start <= timestamp < end; returns the number of rows deleted."""
    if not DeltaTable.is_deltatable(table_path):
        return 0
    iso = "%Y-%m-%dT%H:%M:%S.%fZ"
    predicate = (
        f"symbol = '{symbol}' AND timestamp >= '{start:{iso}}' AND timestamp < '{end:{iso}}'"
    )
    return DeltaTable(table_path).delete(predicate)["num_deleted_rows"]



def delete_symbol(table_path: str, symbol: str) -> int:
    """Delete every row of symbol; returns the number of rows deleted."""
    if not DeltaTable.is_deltatable(table_path):
        return 0
    return DeltaTable(table_path).delete(f"symbol = '{symbol}'")["num_deleted_rows"]
