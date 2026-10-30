"""Silver ingestion orchestration.

Same shape as bronze.ingest but writes to data/silver/ and runs
clean_ohlcv on the way in. Two functions:

  ingest()   clean_ohlcv → save (the convenient one-call entry point)
  save()     wraps storage.upsert with the silver root

Same upsert as bronze. Silver is insert-only by default — once a bar
is cleaned and stored, it doesn't change; update_matched=True is the
explicit full-rebuild path (multicharts.py --full).
"""
import polars as pl

from quantlake.config import SILVER_ROOT
from quantlake.silver.ohlcv import align_to_minute, clean_ohlcv
from quantlake.storage import upsert


def ingest(df: pl.DataFrame, table_name: str, align_1m: bool = False, update_matched: bool = False) -> pl.DataFrame:
    """Clean OHLCV bars and persist them to the silver Delta table.

    Expects df to already carry symbol/year/month partition columns
    (added by bronze.ingest). Re-ingesting the same range is safe: merges
    on (symbol, timestamp) so no duplicates are created.

    ``align_1m=True`` (1-minute bar sources only) first snaps timestamps to
    the minute and collapses the resulting duplicates, see align_to_minute.

    Returns the cleaned DataFrame.
    """
    if df.is_empty():
        return df

    if align_1m:
        df = align_to_minute(df)
    df = clean_ohlcv(df)
    save(df, table_name, update_matched=update_matched)
    return df


def save(df: pl.DataFrame, table_name: str, update_matched: bool = False) -> None:
    """Persist an already-cleaned DataFrame (with partition columns) to the silver Delta table."""
    if df.is_empty():
        return
    upsert(df, str(SILVER_ROOT / table_name), update_matched=update_matched)
