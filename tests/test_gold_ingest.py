import polars as pl

import quantlake.gold.ingest as gold
from helpers import utc


def _bars_at(*timestamps) -> pl.DataFrame:
    return pl.DataFrame({
        "timestamp": pl.Series(list(timestamps), dtype=pl.Datetime("us", "UTC")),
        "close":     [1.0] * len(timestamps),
    })


def test_drops_the_bar_still_in_progress(freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 9, 7, 30))
    df = _bars_at(utc(2024, 1, 2, 8, 55), utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 5))
    out = gold._drop_incomplete_tail(df, "5m")
    assert out["timestamp"].to_list() == [utc(2024, 1, 2, 8, 55), utc(2024, 1, 2, 9, 0)]


def test_bar_is_complete_exactly_at_its_close(freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 9, 5, 0))
    df = _bars_at(utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 5))
    out = gold._drop_incomplete_tail(df, "5m")
    assert out["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0)]


def test_daily_bars(freeze_now):
    freeze_now(gold, utc(2024, 1, 3, 12, 0))
    df = _bars_at(utc(2024, 1, 1), utc(2024, 1, 2), utc(2024, 1, 3))
    out = gold._drop_incomplete_tail(df, "1d")
    assert out["timestamp"].to_list() == [utc(2024, 1, 1), utc(2024, 1, 2)]


def test_unknown_timeframe_keeps_everything(freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 9, 7))
    df = _bars_at(utc(2024, 1, 2, 9, 5))
    assert gold._drop_incomplete_tail(df, "1w").equals(df)
