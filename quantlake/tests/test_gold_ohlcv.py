import polars as pl
import pytest

from helpers import minute_bars, utc
from quantlake.gold.ohlcv import resample, update_features


def test_5m_bars_are_closed_left_label_left():
    # 09:00..09:09 → two 5m bars labelled 09:00 and 09:05
    out = resample(minute_bars(utc(2024, 1, 2, 9, 0), 10), "5m")
    assert out["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 5)]


def test_ohlcv_aggregation():
    out = resample(minute_bars(utc(2024, 1, 2, 9, 0), 10, base=100.0), "5m")
    first = out.row(0, named=True)
    # bars 0..4 of the window
    assert first["open"] == 100.0
    assert first["high"] == 104.5
    assert first["low"] == 99.5
    assert first["close"] == 104.25
    assert first["volume"] == 1 + 2 + 3 + 4 + 5


def test_unaligned_start_goes_into_its_own_window():
    # 09:03..09:06 → 09:00 bar (09:03, 09:04) + 09:05 bar (09:05, 09:06)
    out = resample(minute_bars(utc(2024, 1, 2, 9, 3), 4, base=0.0), "5m")
    assert out["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 5)]
    assert out["open"].to_list() == [0.0, 2.0]
    assert out["volume"].to_list() == [1 + 2, 3 + 4]


def test_symbols_are_resampled_independently():
    start = utc(2024, 1, 2, 9, 0)
    df = pl.concat([
        minute_bars(start, 5, symbol="AAA", base=10.0),
        minute_bars(start, 5, symbol="BBB", base=1000.0),
    ])
    out = resample(df, "5m").sort("symbol")
    assert out["symbol"].to_list() == ["AAA", "BBB"]
    assert out["open"].to_list() == [10.0, 1000.0]
    assert out["close"].to_list() == [14.25, 1004.25]


def test_volume_is_optional():
    out = resample(minute_bars(utc(2024, 1, 2, 9, 0), 5).drop("volume"), "5m")
    assert "volume" not in out.columns
    assert out.height == 1


def test_partition_columns_follow_bar_timestamp():
    # 23:58..00:01 across a month boundary on 1h
    out = resample(minute_bars(utc(2024, 1, 31, 23, 58), 4), "1h")
    assert out["timestamp"].to_list() == [utc(2024, 1, 31, 23, 0), utc(2024, 2, 1, 0, 0)]
    assert out["year"].to_list() == [2024, 2024]
    assert out["month"].to_list() == [1, 2]
    assert out.schema["year"] == pl.Int32
    assert out.schema["month"] == pl.Int8


def test_input_order_does_not_matter():
    df = minute_bars(utc(2024, 1, 2, 9, 0), 10)
    assert resample(df.reverse(), "5m").equals(resample(df, "5m"))


def test_empty_df_is_returned_as_is():
    assert resample(minute_bars(utc(2024, 1, 2), 0), "5m").is_empty()


class _Echo:
    def input_names(self):
        return ["close"]

    def output_names(self):
        return ["f_close"]

    def update(self, inputs):
        return [inputs[0]]


def test_update_features_appends_one_row_of_features():
    bar = resample(minute_bars(utc(2024, 1, 2, 9, 0), 5), "5m")
    out = update_features(bar, _Echo())
    assert out["f_close"].to_list() == bar["close"].to_list()
    assert out.schema["f_close"] == pl.Float64


def test_update_features_rejects_more_than_one_bar():
    bars = resample(minute_bars(utc(2024, 1, 2, 9, 0), 10), "5m")
    with pytest.raises(ValueError):
        update_features(bars, _Echo())
