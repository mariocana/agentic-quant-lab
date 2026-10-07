import polars as pl

from helpers import minute_bars, utc
from quantlake.bronze.ingest import add_partition_columns


def test_adds_symbol_year_month():
    df = minute_bars(utc(2024, 12, 31, 23, 59), 2).drop("symbol")
    out = add_partition_columns(df, "EURUSD")
    assert out["symbol"].to_list() == ["EURUSD", "EURUSD"]
    assert out["year"].to_list() == [2024, 2025]
    assert out["month"].to_list() == [12, 1]
    assert out.schema["year"] == pl.Int32
    assert out.schema["month"] == pl.Int8


def test_stamps_ingested_at_when_missing():
    out = add_partition_columns(minute_bars(utc(2024, 1, 2), 2).drop("symbol"), "X")
    assert out.schema["ingested_at"] == pl.Datetime("us", "UTC")
    assert out["ingested_at"].n_unique() == 1


def test_keeps_existing_ingested_at():
    received = utc(2024, 1, 2, 9, 0, 1)
    df = minute_bars(utc(2024, 1, 2, 9), 1).drop("symbol").with_columns(
        pl.lit(received).cast(pl.Datetime("us", "UTC")).alias("ingested_at")
    )
    out = add_partition_columns(df, "X")
    assert out["ingested_at"][0] == received
