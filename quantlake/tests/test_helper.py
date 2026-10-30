from datetime import datetime, timedelta, timezone

import polars as pl

from quantlake.helper import TF_SECONDS, empty_ohlcv_df, to_utc


def test_naive_datetime_is_assumed_utc():
    out = to_utc(datetime(2024, 1, 2, 9, 0))
    assert out == datetime(2024, 1, 2, 9, 0, tzinfo=timezone.utc)


def test_aware_datetime_is_converted():
    cet = timezone(timedelta(hours=1))
    out = to_utc(datetime(2024, 1, 2, 10, 0, tzinfo=cet))
    assert out == datetime(2024, 1, 2, 9, 0, tzinfo=timezone.utc)
    assert out.tzinfo == timezone.utc


def test_empty_ohlcv_schema():
    df = empty_ohlcv_df()
    assert df.is_empty()
    assert df.schema["timestamp"] == pl.Datetime("us", "UTC")
    assert df.schema["timestamp_close"] == pl.Datetime("us", "UTC")
    for c in ("open", "high", "low", "close", "volume"):
        assert df.schema[c] == pl.Float64


def test_tf_seconds_are_consistent():
    assert TF_SECONDS["1m"] == 60
    assert TF_SECONDS["1d"] == 24 * TF_SECONDS["1h"]
    assert TF_SECONDS["4h"] == 4 * TF_SECONDS["1h"]
